import os
from src.config import TG_BOT_TOKEN, TG_CHAT_ID
from src.args import parse_arguments
from src.utils.file_info import get_file_info
from src.utils.media_info import get_media_info
from src.utils.rclone import upload_files
from src.utils.report import send_report, get_backdrop_url, format_report
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

    :param directory: Path of the folder to process
    :param dry_run: True to simulate the operations without executing them
    """
    files_to_upload = []

    # Parse --rc-upload-to
    upload_to_operation, upload_to_remote = parse_upload_target(args.rc_upload_to)

    # Parse --rc-upload-all (if specified)
    upload_all_operation, upload_all_remote = (
        parse_upload_target(args.rc_upload_all) if args.rc_upload_all else (None, None)
    )

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".mkv", ".mp4", ".avi")):
                file_path = os.path.join(root, file)
                info = get_file_info(file)
                if not info:
                    print(f"Invalid file: {file}")
                    continue

                print(f"Processing file: {file}")

                media_info = get_media_info(file_path)

                # Handle root-relative paths correctly
                relative_path = os.path.relpath(file_path, directory)
                if relative_path.startswith("./"):
                    relative_path = relative_path[2:]  # Remove './' if present

                remote_path = os.path.join(upload_to_remote, relative_path)
                local_path = file_path

                # Upload files
                success = upload_files(
                    local_path=local_path,
                    remote_path=remote_path,
                    config_path=args.rc_config,
                    extra_args=args.rc_args,
                    dry_run=dry_run,
                    operation=upload_to_operation,
                )
                if not success:
                    print(f"Error uploading file: {file}")
                    continue

                # Generate report
                report = format_report(info, media_info, remote_path)

                # Get backdrop URL
                backdrop_url = get_backdrop_url(
                    info["id"], info["id_type"], info["type"]
                )

                # Send report to Telegram
                send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, backdrop_url, dry_run)

                # Add file to the list of files to upload if upload all is specified
                if args.rc_upload_all:
                    files_to_upload.append(file_path)

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


def main() -> None:
    """
    Main entry point. Processes the folder or file specified in the arguments.
    """
    folder_path = args.input.rstrip("/") + "/"
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        exit(1)
    if not os.path.isdir(folder_path):
        print(f"Error: The input path '{folder_path}' is not a valid directory.")
        exit(1)
    if not os.path.isfile(args.rc_config):
        print(
            f"Error: The rclone configuration file '{args.rc_config}' does not exist."
        )
        exit(1)

    process_directory(folder_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
