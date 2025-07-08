import os
import sys
from src.config import TG_BOT_TOKEN, TG_CHAT_ID
from src.args import parse_arguments
from src.utils.file_info import get_file_info
from src.utils.media_info import get_media_info
from src.utils.rclone import upload_files
from src.utils.report import (
    send_report,
    get_backdrop_url,
    format_report,
    format_consolidated_report,
)
import shlex
import tempfile

args = parse_arguments()


def parse_upload_target(target: str):
    """
    Parses the upload target to extract the operation and the remote path.

    :param target: The upload target string in the format "operation,destination"
    :return: A tuple (operation, destination)
    """
    parts = target.split(",", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    else:
        # Default to 'copy' if operation is not specified
        return "copy", parts[0].strip()


def process_directory(directory: str, dry_run: bool = False) -> None:
    """
    Processes a folder and its subfolders to analyze multimedia files.
    Groups episodes by series and season for consolidated reports.

    :param directory: Path of the folder to process
    :param dry_run: True to simulate the operations without executing them
    """
    from collections import defaultdict

    files_to_upload = []
    episodes_by_series = defaultdict(lambda: defaultdict(list))

    # Parse --rc-upload-to
    upload_to_operation, upload_to_remote = parse_upload_target(args.rc_upload_to)

    # Parse --rc-upload-all (if specified)
    upload_all_operation, upload_all_remote = (
        parse_upload_target(args.rc_upload_all) if args.rc_upload_all else (None, None)
    )

    # First pass: collect all episodes and upload files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".mkv", ".mp4", ".avi")):
                file_path = os.path.join(root, file)
                info = get_file_info(file_path)
                if not info:
                    print(f"Invalid file: {file}")
                    continue

                print(f"Processing file: {file}")

                media_info = get_media_info(file_path)

                # Handle root-relative paths correctly
                relative_path = os.path.relpath(file_path, directory)
                if relative_path.startswith("./"):
                    relative_path = relative_path[2:]  # Remove './' if present

                # Get the name of the root folder (e.g. series or movie folder)
                series_folder = os.path.basename(directory.rstrip("/"))

                # Build the remote path including the root folder so that the
                # hierarchy is preserved in the destination remote.
                remote_path = os.path.join(
                    upload_to_remote, series_folder, relative_path
                ).replace(os.sep, "/")
                local_path = file_path

                # Decide the correct rclone operation. For single files we should
                # use "copyto" / "moveto" instead of "copy" / "move" so that the
                # destination includes the full filename. If the user already
                # specified a *to variant we respect it.
                if os.path.isfile(local_path) and upload_to_operation in [
                    "copy",
                    "move",
                ]:
                    operation_to_use = (
                        "copyto" if upload_to_operation == "copy" else "moveto"
                    )
                else:
                    operation_to_use = upload_to_operation

                # Upload files
                success = upload_files(
                    local_path=local_path,
                    remote_path=remote_path,
                    config_path=args.rc_config,
                    extra_args=args.rc_args,
                    dry_run=dry_run,
                    operation=operation_to_use,
                )
                if not success:
                    print(f"Error uploading file: {file}")
                    continue

                # Group episodes by series and season
                if info["type"] == "series":
                    series_key = f"{info['title']} ({info['year']})"
                    season_key = info["season"]
                    episodes_by_series[series_key][season_key].append(
                        {
                            "info": info,
                            "media_info": media_info,
                            "remote_path": remote_path,
                            "episode": int(info["episode"]),
                        }
                    )
                else:
                    # For movies, send individual reports
                    report = format_report(info, media_info, remote_path)
                    backdrop_url = get_backdrop_url(
                        info["id"], info["id_type"], info["type"]
                    )
                    send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, backdrop_url, dry_run)

                # Add file to the list of files to upload if upload all is specified
                if args.rc_upload_all:
                    files_to_upload.append(file_path)

    # Second pass: generate consolidated reports for series
    for series_name, seasons in episodes_by_series.items():
        for season_num, episodes in seasons.items():
            # Sort episodes by episode number
            episodes.sort(key=lambda x: x["episode"])

            # Use first episode's info as base
            base_info = episodes[0]["info"]
            base_remote_path = episodes[0]["remote_path"]

            # Generate consolidated report
            from src.utils.report import format_consolidated_report

            report = format_consolidated_report(episodes, base_remote_path)

            # Get backdrop URL
            backdrop_url = get_backdrop_url(
                base_info["id"], base_info["id_type"], base_info["type"]
            )

            # Send consolidated report to Telegram
            send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, backdrop_url, dry_run)

    # If upload all files is specified, upload them after processing the folder
    if upload_all_remote and files_to_upload:
        relative_files_to_upload = [
            os.path.relpath(file, start=directory).lstrip("./")
            for file in files_to_upload
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            files_from_path = temp_file.name
            for file in relative_files_to_upload:
                temp_file.write(file + "\n")

        try:
            # Upload files using --files-from
            extra_args_with_filter = (
                args.rc_args + f" --files-from {shlex.quote(files_from_path)}"
            )
            upload_files(
                local_path=directory,
                remote_path=upload_all_remote,
                config_path=args.rc_config,
                extra_args=extra_args_with_filter,
                dry_run=dry_run,
                operation=upload_all_operation,
            )
        finally:
            os.remove(files_from_path)


def process_directory_report_only(
    directory: str, remote_base: str, dry_run: bool = False
) -> None:
    """
    Processes a folder to generate reports for existing files without uploading.
    Groups episodes by series and season for consolidated reports.

    :param directory: Path of the local folder to analyze (e.g., /mnt/gdrive/Anime/Series/)
    :param remote_base: Base remote path for reports (e.g., 'gdrive:Anime')
    :param dry_run: True to simulate the operations without sending reports
    """
    from collections import defaultdict

    episodes_by_series = defaultdict(lambda: defaultdict(list))

    # Process all video files in the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".mkv", ".mp4", ".avi")):
                file_path = os.path.join(root, file)
                info = get_file_info(file_path)
                if not info:
                    print(f"Invalid file: {file}")
                    continue

                print(f"Processing file: {file}")

                media_info = get_media_info(file_path)

                # Calculate relative path from the base directory
                relative_path = os.path.relpath(file_path, directory)
                if relative_path.startswith("./"):
                    relative_path = relative_path[2:]  # Remove './' if present

                # Get series folder name (last part of directory path)
                series_folder = os.path.basename(directory.rstrip("/"))

                # Construct remote path including series folder
                remote_path = os.path.join(
                    remote_base, series_folder, relative_path
                ).replace(os.sep, "/")

                # Group episodes by series and season
                if info["type"] == "series":
                    series_key = f"{info['title']} ({info['year']})"
                    season_key = info["season"]
                    episodes_by_series[series_key][season_key].append(
                        {
                            "info": info,
                            "media_info": media_info,
                            "remote_path": remote_path,
                            "episode": int(info["episode"]),
                        }
                    )
                else:
                    # For movies, send individual reports
                    report = format_report(info, media_info, remote_path)
                    backdrop_url = get_backdrop_url(
                        info["id"], info["id_type"], info["type"]
                    )
                    send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, backdrop_url, dry_run)

    # Generate consolidated reports for series
    for series_name, seasons in episodes_by_series.items():
        for season_num, episodes in seasons.items():
            # Sort episodes by episode number
            episodes.sort(key=lambda x: x["episode"])

            # Use first episode's info as base
            base_info = episodes[0]["info"]
            base_remote_path = episodes[0]["remote_path"]

            # Generate consolidated report
            report = format_consolidated_report(episodes, base_remote_path)

            # Get backdrop URL
            backdrop_url = get_backdrop_url(
                base_info["id"], base_info["id_type"], base_info["type"]
            )

            # Send consolidated report to Telegram
            send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, backdrop_url, dry_run)


def main() -> None:
    """
    Main entry point. Processes the folder or file specified in the arguments.
    """
    # Determine if input is a directory or a single file
    input_path = args.input

    if not os.path.exists(input_path):
        print(f"Error: The path '{input_path}' does not exist.")
        sys.exit(1)

    is_directory = os.path.isdir(input_path)

    # For directory paths we normalise with a trailing slash (used elsewhere)
    folder_path = input_path.rstrip("/") + "/" if is_directory else input_path

    if args.report_only:
        if not args.remote_base:
            print("Error: --remote-base is required when using --report-only mode.")
            print("Example: --remote-base 'gdrive:Anime'")
            sys.exit(1)

        if is_directory:
            print(f"Running in report-only mode for: {folder_path}")
            print(f"Remote base path: {args.remote_base}")
            process_directory_report_only(
                folder_path, args.remote_base, dry_run=args.dry_run
            )
        else:
            # Single file report
            from src.utils.file_info import get_file_info
            from src.utils.media_info import get_media_info
            from src.utils.report import (
                format_report,
                get_backdrop_url,
                send_report,
            )

            info = get_file_info(input_path)
            if not info:
                print("Invalid file name format.")
                sys.exit(1)

            # Parse upload target
            upload_to_operation, upload_to_remote = parse_upload_target(args.rc_upload_to)

            print(f"Processing file: {os.path.basename(input_path)}")
            
            media_info = get_media_info(input_path)

            # For series files, preserve directory structure from anime root
            # Find series root folder (contains tvdbid)
            path_parts = input_path.split(os.sep)
            series_folder_idx = None
            for i, part in enumerate(path_parts):
                if '[tvdbid-' in part or '[tmdbid-' in part:
                    series_folder_idx = i
                    break
            
            if series_folder_idx is not None:
                # Preserve structure from series folder onward
                relative_structure = os.sep.join(path_parts[series_folder_idx:])
                remote_path = os.path.join(upload_to_remote, relative_structure).replace(os.sep, "/")
            else:
                # Fallback: just filename
                remote_path = os.path.join(upload_to_remote, os.path.basename(input_path)).replace(os.sep, "/")

            # Use copyto/moveto for single files
            operation = "copyto" if upload_to_operation == "copy" else ("moveto" if upload_to_operation == "move" else upload_to_operation)

            success = upload_files(
                local_path=input_path,
                remote_path=remote_path,
                config_path=args.rc_config,
                extra_args=args.rc_args,
                dry_run=args.dry_run,
                operation=operation,
            )
            
            if not success:
                print(f"Error uploading file: {os.path.basename(input_path)}")
                sys.exit(1)

            # Send report
            report = format_report(info, media_info, remote_path)
            backdrop_url = get_backdrop_url(info["id"], info["id_type"], info["type"])
            send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, backdrop_url, args.dry_run)

    else:
        # Standard mode with file upload
        if not args.rc_upload_to:
            print(
                "Error: --rc-upload-to is required when not using --report-only mode."
            )
            sys.exit(1)
        if not os.path.isfile(args.rc_config):
            print(
                f"Error: The rclone configuration file '{args.rc_config}' does not exist."
            )
            sys.exit(1)
        print(f"Running in upload mode for: {folder_path}")
        process_directory(folder_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
