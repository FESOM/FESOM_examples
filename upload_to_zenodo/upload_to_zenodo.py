#!/usr/bin/env python3
"""
Upload mesh to Zenodo.

Usage::

    $ upload_to_zenodo.py <PATH>
"""

import os
import sys

import click
import questionary
import requests

ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"
"""str : the URL to communicate to the Zenodo API"

DEPOSITION_METADATA = {
    "upload_type": "dataset",
    # FIXME: Something like FESOM2 Meshes should go here
    "communities": [{"identifier": "fesom2_meshes_sandbox_testing"}],
}
"""dict : metadata you want attached to your upload"""


def upload_file(file_path, deposition_bucket, access_token):
    fname = os.path.basename(file_path)
    with open(file_path, "rb") as file:
        response = requests.put(
            f"{deposition_bucket}/{fname}",
            params={"access_token": access_token},
            data=file,
        )
    return response.status_code, response.json()


def add_metadata(deposition_id, access_token, **metadata):
    print("Adding metadata...")
    print({**DEPOSITION_METADATA, **metadata})
    response = requests.put(
        f"{ZENODO_API_URL}/{deposition_id}",
        params={"access_token": access_token},
        json={"metadata": {**DEPOSITION_METADATA, **metadata}},
    )
    return response.status_code, response.json()


def create_deposition(access_token):
    response = requests.post(
        ZENODO_API_URL, params={"access_token": access_token}, json={}
    )
    return response.status_code, response.json()


@click.command()
@click.argument(
    "folder",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--access-token", prompt=True, help="Zenodo access token")
def main(folder, access_token):
    """Upload a folder to Zenodo. The folder path can be provided as an argument or read from stdin if '-' is specified."""
    if not folder:
        folder = questionary.text(
            "Please provide the folder path or use '-' to read from stdin:"
        ).ask()

    if folder == "-":
        folder = sys.stdin.read().strip()

    if not os.path.isdir(folder):
        click.echo("Provided path is not a directory or does not exist.")
        return

    # access_token = questionary.password("Please enter your Zenodo access token:").ask()

    status_code, deposition = create_deposition(access_token)
    if status_code != 201:
        click.echo("Failed to create deposition")
        click.echo(deposition)
        return

    deposition_id = deposition["id"]
    click.echo(f"Created deposition with ID: {deposition_id}")
    deposition_bucket = deposition["links"]["bucket"]

    # Check if folder does not exceed critical size
    critical_size = 50 * 1024 * 1024 * 1024  # 50 GB

    def get_folder_size(folder_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    folder_size = get_folder_size(folder)
    if folder_size > critical_size:
        click.echo(
            f"Folder size exceeds critical size limit of {critical_size / 1024 / 1024 / 1024} GB"
        )
        return

    for root, dirs, files in os.walk(folder):
        if ".git" in dirs:
            dirs.remove(".git")  # Exclude .git folder
        for file in files:
            file_path = os.path.join(root, file)
            status_code, response = upload_file(
                file_path, deposition_bucket, access_token
            )
            if status_code != 201:
                click.echo(f"Failed to upload {file_path}")
                click.echo(response)
            else:
                click.echo(f"Uploaded {file_path}")

    status_code, response = add_metadata(
        deposition_id, access_token, title=f"FESOM2 Mesh: {folder}"
    )
    if status_code != 200:
        click.echo("Failed to add metadata")
        click.echo(response)
    else:
        click.echo("Added metadata successfully")

    click.echo(
        f"Done! You can finalize your deposition on Zenodo: {deposition['links']['html']}"
    )


if __name__ == "__main__":
    main()
