"""Generate Radical HR caricatures with Gemini.

Usage: python3 tools/generate.py <style> <out_dir> [idea ...]
"""
import base64, json, subprocess, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Vertex AI, billed to the Google Cloud project; auth via the local gcloud login.
PROJECT = "lillefar-com"
MODEL = "gemini-2.5-flash-image"
ENDPOINT = (f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT}/locations/global"
            f"/publishers/google/models/{MODEL}:generateContent")

def api_key():
    return subprocess.run(["gcloud", "auth", "print-access-token"],
                          capture_output=True, text=True, check=True).stdout.strip()

STYLES = {
    "ink": "Grotesque editorial pen-and-ink caricature in the tradition of Ralph Steadman and Gerald Scarfe. "
           "Wildly exaggerated anatomy: enormous heads, tiny bodies, bulging eyes, huge noses, splattered ink, "
           "loose scratchy linework, black ink on off-white paper with a single splash of red.",
    "propaganda": "1950s mid-century corporate propaganda poster illustration. Cheerful, smiling, square-jawed "
                  "office workers with sinister undertones. Limited palette of cream, teal, mustard and tomato red, "
                  "halftone shading, slightly faded print.",
    "newspaper": "Gritty old-school political newspaper cartoon. Heavy crosshatching, sweaty grotesque characters "
                 "with oversized heads and bulbous noses, dramatic expressions, black ink only, grayscale wash.",
    "riso": "Flat risograph print illustration with two clashing inks (fluorescent pink and deep blue), "
            "visible misregistration between layers, grainy texture, bold simplified caricature shapes, "
            "exaggerated proportions, modern indie zine aesthetic.",
    "rubberhose": "1930s rubber-hose cartoon style like early animated shorts. Noodle limbs, white gloves, "
                  "pie-cut eyes, unsettling permanent grins, vintage film grain, sepia and black ink.",
}

IDEAS = {
    "parking": "A tiny parking lot with only two spaces, both taken. A panicked, sweaty office worker in a suit "
               "sprints across the lot at dawn clutching car keys. A large clock shows 5:47. A smug red 'P' sign.",
    "paycut": "A salary meeting. A grinning manager slides a contract across the desk with '-7.5%' in huge red "
              "letters. The employee across the desk is horrified, holding a pen. A desk calendar shows '5 DAYS'.",
    "phones": "A wooden box mounted on the wall next to a toilet door, overflowing with confiscated smartphones, "
              "labeled 'PHONES'. A forlorn office worker walks into the toilet empty-handed. A sign reads "
              "'HYGIENE POLICY'.",
    "applicant": "A smug manager holds up a glowing resume with five gold stars and a photo of an impossibly "
                 "perfect young genius, showing it to a nervous employee at her desk who is sweating and "
                 "clutching her coffee mug.",
    "christmas": "A festive company Christmas party in the office, decorated with a tree and tinsel. A beaming "
                 "manager in a Santa hat welcomes a queue of visibly nervous male employees in suits toward a "
                 "doctor in a white coat holding a giant pair of scissors. A banner reads 'XMAS SNIP PARTY' and "
                 "a sign reads 'GROUP DISCOUNT'. Each man in the queue clutches a pay slip reading '+RAISE'.",
    "afternoon": "A cheerful open-plan office at 2 o'clock on a weekday. Rosy-cheeked employees raise beer mugs "
                 "at their desks while a wall clock shows 2:00. A rising sales chart on the wall.",
    "esteem": "A manager hoists a delighted employee high onto a tall pedestal labeled 'STAR', while holding "
              "a saw behind his back, about to cut the pedestal's leg.",
    "cold": "An icy office with frost on the windows and icicles hanging from the ceiling lamps. Shivering "
            "employees in scarves, mittens and wooly hats type at their desks. A locked thermostat reads '15°'.",
    "value": "A grinning manager pops his head over a cubicle wall with a huge speech bubble reading "
             "'VALUE TODAY?'. The startled employee at the desk jumps out of her chair. A dozen sticky notes "
             "on her monitor read 'VALUE?'.",
    "toiletpaper": "A heroic, glowing roll of soft toilet paper on a pedestal, radiating golden light like a "
                   "sacred relic. Office workers kneel before it in blissful gratitude.",
    "pregnancy": "An HR lady with binoculars peeks out from behind a potted office plant, spying on a young "
                 "female employee at the coffee machine who is choosing decaf. A clipboard in the HR lady's "
                 "lap has a checklist.",
    "handle": "A grinning manager in a suit firmly rattles the handle of a locked office toilet door marked "
              "'WC' with a red 'OCCUPIED' indicator, holding a stopwatch in his other hand.",
    "afterwork": "Weary office workers in party hats slump at their desks under a festive banner reading "
                 "'AFTERWORK FUN'. A wall clock shows 7:30 in the evening. Uneaten pizza boxes go cold.",
    "joke": "Split panel of the same manager: on the left he is laughing heartily, slapping a new hire on "
            "the back; on the right, one second later, he stares at the new hire with a dead serious face. "
            "The new hire is confused in both.",
    "sneeze": "A company canteen divided by a velvet rope. Healthy, smiling employees eat lunch at a table "
              "while a queue of sniffling, green-faced employees with tissues waits behind the rope under "
              "a sign 'PLEASE WAIT'.",
    "messenger": "A manager shrugs innocently with both palms up, pointing his thumb at a signpost arrow "
                 "reading 'ASK HR'. The arrow points to a closed door with a sign 'BACK IN 3 WEEKS'. "
                 "A confused employee holds a question mark.",
    "ventilation": "A stuffy team room with sealed, boarded-up windows and visible green stink clouds. "
                   "Employees hold their noses and hurry out of the room back to their desks.",
    "survey": "A beaming HR manager hands out a survey on a clipboard. The only answer choices are "
              "'AMAZING', 'VERY AMAZING' and 'LIFE-CHANGING'. A big '100%' stamp in the corner.",
    "language": "Two employees whisper and giggle by the water cooler, gossiping about their manager. "
                "The manager stands right behind them with an enormous cupped ear and a knowing smirk, "
                "taking notes in a small notebook.",
}

PROMPT = ("Satirical caricature illustration for a website about absurd, cruel HR policies. "
          "Scene: {idea} Style: {style} Landscape composition, single panel, no borders, no captions, "
          "only the short words mentioned in the scene.")

def generate(style, idea_key, idea, out_dir, key):
    body = {
        "contents": [{"role": "user", "parts": [{"text": PROMPT.format(idea=idea, style=STYLES[style])}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "4:3"}},
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 3:
                raise
            time.sleep(15 * (attempt + 1))
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            ext = "png" if "png" in part["inlineData"]["mimeType"] else "jpg"
            path = out_dir / f"{idea_key}.{ext}"
            path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
            return f"ok   {style}/{path.name}"
    return f"FAIL {style}/{idea_key}: {json.dumps(data)[:300]}"

def main():
    style, out_dir, *keys = sys.argv[1:]
    styles = list(STYLES) if style == "all" else [style]
    ideas = {k: IDEAS[k] for k in (keys or IDEAS)}
    key = api_key()
    jobs = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for s in styles:
            d = Path(out_dir) / s
            d.mkdir(parents=True, exist_ok=True)
            for k, idea in ideas.items():
                if not keys and any(d.glob(f"{k}.*")):
                    continue  # rerun without idea keys only fills gaps
                jobs.append(pool.submit(generate, s, k, idea, d, key))
        for j in jobs:
            try:
                print(j.result())
            except Exception as e:
                print("FAIL", e)

if __name__ == "__main__":
    main()
