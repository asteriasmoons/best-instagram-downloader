import instaloader
import time
import requests
import urllib.parse
import json
from variables import *

# === Instaloader Settings ===
SESSION_FILE = "session-asteriasmoons"
USERNAME = "asteriasmoons"


def get_instaloader_media_links(shortcode):
    L = instaloader.Instaloader()
    try:
        L.load_session_from_file(USERNAME, SESSION_FILE)
    except Exception as e:
        print(f"[HYBRID] Failed to load session file: {e}")
        return None, None, "Failed to load session"

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        print(f"[HYBRID] Instaloader error: {e}")
        # Instaloader rate limit message
        if "Please wait a few minutes" in str(e):
            return None, None, "RATE_LIMIT"
        return None, None, str(e)

    media_links = []
    caption = post.caption or ""

    try:
        if post.typename == "GraphSidecar":
            for node in post.get_sidecar_nodes():
                if node.is_video:
                    media_links.append({"type": "video", "url": node.video_url})
                else:
                    media_links.append({"type": "image", "url": node.display_url})
        elif post.is_video:
            media_links.append({"type": "video", "url": post.video_url})
        else:
            media_links.append({"type": "image", "url": post.url})
    except Exception as e:
        print(f"[HYBRID] Error processing Instaloader media: {e}")
        return None, None, str(e)

    time.sleep(8)  # Cooldown!
    print(f"[HYBRID] Instaloader success for {shortcode}: {media_links}")
    return media_links, caption, None


# --- Legacy method (Fallback) ---


def generate_request_body(shortcode):
    # This is your "giant dictionary" from previous code, used for the POST request body.
    return urllib.parse.urlencode(
        {
            "av": "0",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "b",
            "__hs": "20183.HYP:instagram_web_pkg.2.1...0",
            "dpr": "3",
            "__ccg": "GOOD",
            "__rev": "1021613311",
            "__s": "hm5eih:ztapmw:x0losd",
            "__hsi": "7489787314313612244",
            "__dyn": "7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJw5ux609vCwjE1EE2Cw8G11wBz81s8hwGxu786a3a1YwBgao6C0Mo2swtUd8-U2zxe2GewGw9a361qw8Xxm16wa-0oa2-azo7u3C2u2J0bS1LwTwKG1pg2fwxyo6O1FwlA3a3zhA6bwIxe6V8aUuwm8jwhU3cyVrDyo",
            "__csr": "goMJ6MT9Z48KVkIBBvRfqKOkinBtG-FfLaRgG-lZ9Qji9XGexh7VozjHRKq5J6KVqjQdGl2pAFmvK5GWGXyk8h9GA-m6V5yF4UWagnJzazAbZ5osXuFkVeGCHG8GF4l5yp9oOezpo88PAlZ1Pxa5bxGQ7o9VrFbg-8wwxp1G2acxacGVQ00jyoE0ijonyXwfwEnwWwkA2m0dLw3tE1I80hCg8UeU4Ohox0clAhAtsM0iCA9wap4DwhS1fxW0fLhpRB51m13xC3e0h2t2H801HQw1bu02j-",
            "__comet_req": "7",
            "lsd": "AVrqPT0gJDo",
            "jazoest": "2946",
            "__spin_r": "1021613311",
            "__spin_b": "trunk",
            "__spin_t": "1743852001",
            "__crn": "comet.igweb.PolarisPostRoute",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PolarisPostActionLoadPostQueryQuery",
            "variables": json.dumps(
                {
                    "shortcode": shortcode,
                    "fetch_tagged_user_count": None,
                    "hoisted_comment_id": None,
                    "hoisted_reply_id": None,
                }
            ),
            "server_timestamps": "true",
            "doc_id": "8845758582119845",
        }
    )


def get_legacy_media_links(shortcode):
    url = "https://www.instagram.com/graphql/query"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-FB-Friendly-Name": "PolarisPostActionLoadPostQueryQuery",
        "X-BLOKS-VERSION-ID": "0d99de0d13662a50e0958bcb112dd651f70dea02e1859073ab25f8f2a477de96",
        "X-CSRFToken": "uy8OpI1kndx4oUHjlHaUfu",
        "X-IG-App-ID": "1217981644879628",
        "X-FB-LSD": "AVrqPT0gJDo",
        "X-ASBD-ID": "359341",
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Referer": "https://www.instagram.com/",
    }
    data = generate_request_body(shortcode)
    try:
        response = requests.post(url, headers=headers, data=data, proxies=warp_proxies)
        response.raise_for_status()
        json_response = response.json()
    except Exception as e:
        print(f"[HYBRID] Legacy scraper failed: {e}")
        return [], None

    media_links = []
    caption = None
    try:
        media = json_response["data"]["xdt_shortcode_media"]
        # caption
        caption = (
            media.get("edge_media_to_caption", {})
            .get("edges", [{}])[0]
            .get("node", {})
            .get("text", "")
        )
        # Check if it's a sidecar (multiple media)
        if (
            media.get("__typename") == "XDTGraphSidecar"
            and "edge_sidecar_to_children" in media
        ):
            edges = media["edge_sidecar_to_children"]["edges"]
            for edge in edges:
                node = edge["node"]
                media_type = "video" if node.get("is_video", False) else "image"
                if media_type == "video":
                    url = node.get("video_url")
                else:
                    display_resources = node.get("display_resources", [])
                    if display_resources:
                        url = display_resources[-1]["src"]
                    else:
                        url = node.get("display_url")
                media_links.append({"type": media_type, "url": url})
        else:
            media_type = "video" if media.get("is_video", False) else "image"
            if media_type == "video":
                url = media.get("video_url")
            else:
                display_resources = media.get("display_resources", [])
                if display_resources:
                    url = display_resources[-1]["src"]
                else:
                    url = media.get("display_url")
            media_links.append({"type": media_type, "url": url})
    except Exception as e:
        print(f"[HYBRID] Error extracting legacy media info: {e}")
    print(f"[HYBRID] Legacy scraper result for {shortcode}: {media_links}")
    return media_links, caption


# === HYBRID FUNCTION ===
def get_instagram_media_links(shortcode):
    # 1. Try Instaloader first
    media_links, caption, error = get_instaloader_media_links(shortcode)
    if media_links:
        return media_links, caption

    # 2. If Instaloader failed, try legacy
    print(f"[HYBRID] Instaloader failed ({error}), falling back to legacy scraper...")
    media_links, caption = get_legacy_media_links(shortcode)
    return media_links, caption