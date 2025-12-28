def generate_hashtags(input_text):
    words = input_text.lower().split()[:5]
    base = ["fyp", "viral", "trending", "foryou", "explore", "tiktok"]
    variants = [word + str(i) for word in words for i in ["", "1", "2", "official"]]
    all_tags = base + words + variants + [input_text.replace(" ", "")]
    unique = list(dict.fromkeys(all_tags))[:30]
    return [f"#{tag}" for tag in unique]

# Add more tool functions here for other platforms, e.g., caption_optimizer, script_generator
