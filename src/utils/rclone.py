import os
import subprocess


def construct_remote_path(base_remote: str, relative_path: str) -> str:
    """
    Constructs the full remote path based on the base remote path and the relative path.

    :param base_remote: Base remote path (e.g., 'copias_fc4:Anime/')
    :param relative_path: Relative path to append to the base remote path
    :return: Full remote path
    """
    if not base_remote.endswith("/"):
        base_remote += "/"
    return os.path.join(base_remote, relative_path).replace("\\", "/")


def upload_files(
    local_path: str,
    remote_path: str,
    config_path: str,
    extra_args: str,
    dry_run: bool,
    operation: str,
) -> bool:
    """
    Uploads files to the cloud using rclone.

    :param local_path: Local path of the files
    :param remote_path: Remote path where to upload the files
    :param config_path: Path to the rclone configuration file
    :param extra_args: Additional arguments for rclone
    :param dry_run: True to simulate the upload without executing it
    :param operation: The rclone operation to perform (e.g., 'copy', 'copyto', 'move', 'moveto')
    :return: True if the upload was successful, False otherwise
    """

    if operation not in ["copy", "copyto", "move", "moveto"]:
        print(f"Invalid operation: {operation}")
        return False

    command = [
        "rclone",
        operation,
        local_path,
        remote_path,
        "-P",
        "--config",
        config_path,
    ]

    if extra_args:
        command.extend(extra_args.split())

    print(f"Uploading files: {local_path} -> {remote_path} with operation {operation}")

    if dry_run:
        print("Upload simulation with the command:")
        print(" ".join(command))
        return True
    else:
        try:
            result = subprocess.run(command, check=True)
            if result.returncode == 0:
                print(f"Upload completed: {local_path} -> {remote_path}")
                return True
            else:
                print(f"Error uploading files: Return code {result.returncode}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error uploading files: {e}")
            return False
