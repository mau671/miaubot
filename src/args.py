import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process folders and video files.")
    parser.add_argument("-i", "--input", required=True, help="Root folder to analyze")
    parser.add_argument(
        "--rc-config",
        required=False,
        default="rclone.conf",
        help="Path to the rclone configuration file",
    )
    parser.add_argument(
        "--rc-args",
        required=False,
        default="",
        help="Additional arguments for rclone (as string)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the upload without making calls",
    )
    parser.add_argument(
        "--rc-upload-to",
        required=False,
        help="Name of the remote (with its path) configured in rclone",
    )
    parser.add_argument(
        "--rc-upload-all",
        required=False,
        help="Upload all found files",
    )
    return parser.parse_args()
