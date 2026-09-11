from erklaerbaer.config import load_settings
from erklaerbaer.science_review import review_science
from erklaerbaer.storyboards import load_storyboard, save_storyboard

settings = load_settings()
for topic, lang in [
    ("springende-muenze", "de-DE"),
    ("karton-gitarre", "nl-NL"),
    ("krabbeltier-safari", "nl-NL"),
]:
    path = next((settings.project_root / "storyboards" / topic / lang).glob("*.json"))
    board = load_storyboard(path)
    review = review_science(board, settings)
    save_storyboard(board.model_copy(update={"review": review}), path)
    print(topic, review.model_dump(), flush=True)
