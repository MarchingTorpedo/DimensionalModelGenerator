"""Example client to upload files to the MCP server and save returned ZIP."""
import argparse
import requests
import os


def main(url, files, api_key=None, out="datamodel_outputs.zip"):
    with open(files[0], "rb") as f:
        pass
    mfiles = [("files", (os.path.basename(f), open(f, "rb"))) for f in files]
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    resp = requests.post(url, files=mfiles, headers=headers)
    for _, fh in mfiles:
        fh[1].close()

    if resp.status_code != 200:
        print("Error:", resp.status_code, resp.text)
        return
    with open(out, "wb") as f:
        f.write(resp.content)
    print("Saved:", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:9000/generate")
    p.add_argument("--out", default="datamodel_outputs.zip")
    p.add_argument("--api-key", default=None)
    p.add_argument("files", nargs="+", required=True)
    args = p.parse_args()
    main(args.url, args.files, api_key=args.api_key, out=args.out)
