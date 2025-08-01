import instaloader
import time

SESSION_FILE = "session-asteriasmoons"
USERNAME = "asteriasmoons"


def get_instagram_media_links(shortcode):
    L = instaloader.Instaloader()
    try:
        L.load_session_from_file(USERNAME, SESSION_FILE)
    except Exception as e:
        print(f"[DEBUG] Failed to load session file: {e}")
        return [], None

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        print(f"[ERROR] Could not fetch post for shortcode {shortcode}: {e}")
        return [], None

    media_links = []
    caption = post.caption or ""

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

    print(f"[DEBUG] Media links for {shortcode}: {media_links}")
    print(f"[DEBUG] Caption: {caption[:100]}...")

    time.sleep(3)  # 🕑 Delay for 3 seconds after each request

    return media_links, caption