"""Seed the resources table from the CVW WordPress site content.

Run from the project root:
    source .venv/bin/activate
    python scripts/seed_resources.py

Idempotent: skips any resource whose (category, title) already exists.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.resource import Resource

RESOURCES = [
    # ── Safety First! ──────────────────────────────────────────────────────────
    ("Safety First!", "Toxic Woods",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2025/11/toxic_woods.pdf",
     "PDF — toxic wood species reference"),
    ("Safety First!", "Wood Allergies and Toxicity",
     "https://www.wood-database.com/wood-articles/wood-allergies-and-toxicity/",
     "Reference guide for wood safety concerns"),
    ("Safety First!", "Lathe Safety Guidelines",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Lathe-Safety-Guidelines.pdf",
     "Official safety protocols for lathe operation"),
    ("Safety First!", "Bandsaw Safety Guidelines",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Band-Saw-Safety.pdf",
     "Safety procedures for bandsaw use"),
    ("Safety First!", "AAW Safety Guidebook",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/SafetyGuidebook20160323.pdf",
     "American Association of Woodturners safety resource"),
    ("Safety First!", "Safety Matters From the Eye of a Survivor",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/AMWoodturnerJune2014.pdf",
     "First-person account — American Woodturner, June 2014"),

    # ── Mentoring Information ───────────────────────────────────────────────────
    ("Mentoring Information", "Club Mentors",
     "https://centralvawoodturners.org/saturday-skill-sessions/",
     "CVW volunteer mentors available for assistance"),
    ("Mentoring Information", "AAW Teaching Woodturning Basics V2",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2023/05/TeachingWoodturningBasicsV2.pdf",
     "Essential instructional document"),
    ("Mentoring Information", "Resources for Learning to Turn (Jeff Corwin)",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2024/04/Resources-for-learning-to-turn-Corrected.pdf",
     "Curated learning resource list"),
    ("Mentoring Information", "Words to Turn By",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/words-to-turn-by.pdf",
     "Mentoring guidance document"),
    ("Mentoring Information", "Some Thoughts on Professional Development and Presentation",
     "http://centralvawoodturners.org/info-pages/Professional%20Presentation%20revised.pdf",
     "Professional development guide"),
    ("Mentoring Information", "Demo Tips",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/CVWs-Demo-TipsJan2014.pdf",
     "Demonstration best practices from CVW"),
    ("Mentoring Information", "CVW Video System",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Skil-Center-Video-Layout.pdf",
     "Technical documentation for video demonstrations"),

    # ── Sanding and Sharpening ─────────────────────────────────────────────────
    ("Sanding and Sharpening", "Sharpening Lathe Tools for CVW Binder",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2024/05/Sharpening-Lathe-Tools-for-CVW-Binder-Final-Version-K.-Koons-May-2024.docx",
     "Comprehensive sharpening guide by K. Koons"),
    ("Sanding and Sharpening", "Sharpening Guide from Carter & Sons",
     "https://carterandsontoolworks.com/pages/woodturning-resources",
     "Professional tool sharpening resources"),
    ("Sanding and Sharpening", "An Introduction to Sharpening",
     "https://www.qgdigitalpublishing.com/publication/?m=59376&i=779541&p=20&ver=html5",
     "Dennis Belcher — AAW, February 2003"),
    ("Sanding and Sharpening", "3M Scotch-Brite Sanding Pads",
     "http://centralvawoodturners.org/3m-scotch-britesanding-pads/",
     "Product information and applications"),
    ("Sanding and Sharpening", "Sharpening Demystified",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Sharpening-Demystified-Kirk-DeHeer-AAW-2006.pdf",
     "Kirk DeHeer — AAW 2006 presentation"),
    ("Sanding and Sharpening", "Nate Hawkes on Sanding and Sanding Supplies",
     "http://centralvawoodturners.org/sanding-and-sanding-supplies/",
     "Expert perspective on sanding materials"),

    # ── Finishing ─────────────────────────────────────────────────────────────
    ("Finishing", "Food Safe Finishes",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Food-Safe-Finishes.pdf",
     "Guide to food-safe finishing techniques"),

    # ── Beginners Sites ───────────────────────────────────────────────────────
    ("Beginners Sites", "Brian Clifford's Introduction to Woodturning",
     "http://www.turningtools.co.uk/wtintro/wtintro.html",
     "Foundational turning instruction"),
    ("Beginners Sites", "Kent's Turn a Wood Bowl",
     "https://turnawoodbowl.com",
     "Specialized bowl turning guidance"),
    ("Beginners Sites", "Beginner's — Organic Lesson",
     "http://www.organiclesson.com/wood-lathe-diy-wood-projects/",
     "Introduction to wood lathe and DIY projects"),

    # ── Tools ─────────────────────────────────────────────────────────────────
    ("Tools", "Guide To Gouges",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Guidetogouges.pdf",
     "Comprehensive gouge reference document"),
    ("Tools", "Tools Explained",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Tools-Explained.pdf",
     "Turning tool identification and use"),
    ("Tools", "Scraper Magic Info",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Scrapers.pdf",
     "Scraper tool techniques and applications"),
    ("Tools", "Vacuum Chuck System",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/vacuum-system.pdf",
     "Vacuum holding systems for turning"),
    ("Tools", "Texturing Tools for Wood Turning",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Texturing-Tools-Pettigrew-July-2016.pdf",
     "Alex Pettigrew's texturing tool guide"),
    ("Tools", "Interesting Homemade Lathe",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/BowlLathe.pdf",
     "DIY lathe construction project"),
    ("Tools", "Another Homemade Lathe",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Lathe2.pdf",
     "Alternative lathe design"),
    ("Tools", "Freds Homemade Lathe",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/FW-Lathe.pdf",
     "Fred's custom lathe documentation"),

    # ── Maintenance ───────────────────────────────────────────────────────────
    ("Maintenance", "Ten Steps to a Smooth Lathe",
     "https://aaow.informz.net/aaow/data/images/20250819%20WF0902p16-23%20Belcher%20Ten%20Steps.pdf",
     "Dennis Belcher's lathe maintenance article"),
    ("Maintenance", "Lathe and Chuck Maintenance",
     "https://www.youtube.com/watch?v=G0DQIMVYYvs",
     "Jim Rogers video tutorial on maintenance"),

    # ── Wood Preparation for Turning ──────────────────────────────────────────
    ("Wood Preparation", "Bowl Blanks From Log",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2024/04/Bowl-Blanks-From-Log.pdf",
     "Guide to cutting blanks with grain orientation"),
    ("Wood Preparation", "Producing Spalted Woods",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/PRODUCING-SPALTED-WOODS-7-19-2016.pdf",
     "Dennis Hippen's spalting techniques"),
    ("Wood Preparation", "Avoiding Cracks in Bowls and Hollow Forms",
     "http://www.aawexplo.wwwmi3-ss30.a2hosted.com/aaw_cs1_pdf/AW3004p17-19.pdf",
     "Techniques for preventing wood checking"),
    ("Wood Preparation", "Wood Identification Site",
     "http://www.hobbithouseinc.com/personal/woodpics/",
     "Visual wood species reference database"),
    ("Wood Preparation", "One-Way Coring System Club Demo",
     "https://youtu.be/eKidKIPevjE",
     "Video demonstration by Jim and Norm"),
    ("Wood Preparation", "How-to Guide for Coring System",
     "https://turnawoodbowl.com/oneway-coring-system-easy-core-bowl-how-to-guide-illustrated/",
     "Kent Weakley's illustrated instructions"),
    ("Wood Preparation", "101 Handy Sites for Conscientious Wood Use",
     "http://forestrydegree.net/conscientious-wood-use/",
     "Sustainable wood sourcing resources"),

    # ── Turning Tips and Information ──────────────────────────────────────────
    ("Turning Tips", "Multi-Sided Boxes",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2025/10/multi-sided.pdf",
     "Gary Peterson's box turning techniques"),
    ("Turning Tips", "Two Step Turning Process",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2023/09/Two-Step-Turning-Process-2023.08.16.docx",
     "Tom Wirsing's methodical approach"),
    ("Turning Tips", "Turn a Large Platter Process Steps",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2023/09/Turn-a-Large-Platter-Process-Steps-2023.08.16.doc",
     "Tom Wirsing's platter turning guide"),
    ("Turning Tips", "Hipwood's Pen Making Guide",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2023/02/Hipwoods-Pen-Making-Guide-Feb-2023.pdf",
     "Complete pen turning instruction"),
    ("Turning Tips", "Grain Direction",
     "http://www.aawexplo.wwwmi3-ss30.a2hosted.com/aaw_cs1_pdf/WF0703p4-12.pdf",
     "Understanding wood grain orientation"),
    ("Turning Tips", "Mike Peace Video on Wood Grain",
     "https://www.youtube.com/watch?v=QDaSD3S1pCY&feature=youtu.be",
     "Video instruction on grain dynamics"),
    ("Turning Tips", "Voids, What to do",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/VOIDS-What-to-do.pdf",
     "Tom Evans' void remediation techniques"),
    ("Turning Tips", "Steps To Follow In Making A Platter",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/STEPS-TO-FOLLOW-IN-MAKING-A-PLATTER.pdf",
     "Ervin Stutzman's platter process"),
    ("Turning Tips", "Natural Edge Bowls",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/tom_boley_nat_bowls.pdf",
     "Tom Boley's natural edge techniques"),
    ("Turning Tips", "Multi-Axis Part 1",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/multiaxis1_dill.pdf",
     "Barbara Dill's multi-axis introduction"),
    ("Turning Tips", "Multi-Axis Part 2",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/multiaxis2_dill.pdf",
     "Barbara Dill's advanced multi-axis techniques"),
    ("Turning Tips", "Hollowing Through the Bottom",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Bottom_hollowing.pdf",
     "Dick Hines' hollowing methodology"),
    ("Turning Tips", "Coloring and Texturing — Edging & Inlay",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Coloring-demo-edging-and-inlay.pdf",
     "Richard Landreth's decorative techniques"),
    ("Turning Tips", "Coloring and Texturing — Grain Filling",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Coloring-demo-grain-filling.pdf",
     "Richard Landreth's grain filling methods"),
    ("Turning Tips", "Coloring and Texturing — Wood Coloring",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Wood-Coloring-demo.pdf",
     "Richard Landreth's wood coloring guide"),
    ("Turning Tips", "Wood Cracks Article",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Wood-Cracks-Article.pdf",
     "Dennis Belcher's crack prevention guide"),
    ("Turning Tips", "Bowl Talk",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/bowl_talk_may08.pdf",
     "Bowl turning discussion and techniques"),
    ("Turning Tips", "YouTube Woodturning Videos",
     "http://www.youtube.com/results?search_query=woodturning&search_type=&aq=f",
     "YouTube search results for woodturning"),

    # ── Schools ───────────────────────────────────────────────────────────────
    ("Schools", "Arrowmont in Gatlinburg, TN",
     "https://arrowmont.org",
     "Residential woodturning instruction program"),
    ("Schools", "John C. Campbell School in North Carolina",
     "https://www.folkschool.org",
     "Folk school craft instruction"),

    # ── Projects ──────────────────────────────────────────────────────────────
    ("Projects", "Quick Boxes",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/quick_boxes.pdf",
     "Jim Vogel's box project instructions"),
    ("Projects", "Fishing Lures",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Fishing_lures.pdf",
     "Ray Kallman's lure turning guide"),
    ("Projects", "Mystery Salt Urn",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/nick_cook_mystery_salt_urn.pdf",
     "Nick Cook's specialty vessel project"),
    ("Projects", "Pepper Mills",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/nick_cook_peppermills.pdf",
     "Nick Cook's pepper mill designs"),
    ("Projects", "Chip Carving",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/central-VA-woodturners-talk.pptx",
     "Jeff Fleisher's chip carving presentation"),
    ("Projects", "Protruding Wave Bowl Directions",
     "http://centralvawoodturners.org/cvwwp/wp-content/uploads/2020/10/Directions-for-Protruding-wave-bowl.pdf",
     "John Beaver's wave bowl project"),
    ("Projects", "Dry Wood Wave Bowl Directions",
     "http://centralvawoodturners.org/cvwwp/wp-content/uploads/2020/10/Directions-for-Dry-wave-bowl.pdf",
     "John Beaver's dry wood wave project"),
    ("Projects", "Hipwood's Pen Making Guide",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2023/02/Hipwoods-Pen-Making-Guide-Feb-2023.pdf",
     "Complete pen turning instruction"),

    # ── Marketing Your Art ────────────────────────────────────────────────────
    ("Marketing Your Art", "Finding Your Own Market",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/CVW-Panel-Discussion-Finding-Your-Own-Market.pdf",
     "Mike Sorge's panel discussion notes"),
    ("Marketing Your Art", "Marketing Tips",
     "https://centralvawoodturners.org/cvwwp/wp-content/uploads/2021/04/Wood-Turning-Marketing.pdf",
     "Phil Evans' marketing strategies"),
    ("Marketing Your Art", "Etsy",
     "http://www.etsy.com/",
     "Online marketplace for handmade goods"),
    ("Marketing Your Art", "Studio Photography Guide",
     "https://wp.fredwilliamson.com/wp-content/uploads/2024/03/Making-a-Studio-Photo-of-Your-Bowl-final.pdf",
     "Fred Williamson's product photography guide"),
    ("Marketing Your Art", "Studio Photography Notes",
     "https://wp.fredwilliamson.com/wp-content/uploads/2024/03/Notes-for-Studio-Photography-edited-1.pdf",
     "Fred Williamson's photography notes"),

    # ── Woodturner Inspiration Sites ──────────────────────────────────────────
    ("Inspiration Sites", "American Association of Woodturners",
     "http://woodturner.org/",
     "Professional woodturning organization"),
    ("Inspiration Sites", "Nick Cook Woodturner",
     "http://www.nickcookwoodturner.com/",
     "Professional turner's portfolio"),
    ("Inspiration Sites", "Barbara Dill",
     "http://www.barbaradill.com/",
     "Multi-axis turning specialist"),
    ("Inspiration Sites", "David Ellsworth Studios",
     "http://www.ellsworthstudios.com/",
     "Hollowform turning master"),
    ("Inspiration Sites", "Richard Raffan",
     "http://www.richardraffan.com/",
     "Internationally recognized turner"),
    ("Inspiration Sites", "The Wood Shop TV",
     "http://thewoodshop.tv/",
     "Woodturning video website"),

    # ── Club Member Sites ─────────────────────────────────────────────────────
    ("Club Member Sites", "Roger Chandler",
     "http://www.artisticwoodtreasures.com/",
     "CVW member's turning portfolio"),
    ("Club Member Sites", "Kirk McCauley",
     "http://kirkmccauley.com/",
     "CVW member's work and gallery"),
    ("Club Member Sites", "Mike Sorge",
     "http://www.mikesorge.com/",
     "CVW member's turning creations"),
    ("Club Member Sites", "Fred Williamson Bowls",
     "http://www.fredwilliamson.com/",
     "CVW member's bowl turning work"),

    # ── Other Club Websites ───────────────────────────────────────────────────
    ("Other Club Websites", "Capital Area Woodturners",
     "http://www.capwoodturners.org/",
     "Washington DC area club"),
    ("Other Club Websites", "Tidewater Turners of Virginia",
     "http://www.tidewaterturners.net/",
     "Virginia regional club"),
    ("Other Club Websites", "Woodturners of the Virginias",
     "http://www.woodturnersofthevirginias.org/index.htm",
     "Virginia regional organization"),
    ("Other Club Websites", "Tennessee Association of Woodturners",
     "http://tnwoodturners.org/",
     "Tennessee woodturning organization"),
    ("Other Club Websites", "Apple Valley Woodturners",
     "http://www.applevalleywoodturners.org/",
     "Regional woodturning club"),
    ("Other Club Websites", "Chicago Woodturners",
     "http://www.chicagowoodturners.com/",
     "Illinois woodturning club"),
    ("Other Club Websites", "Cumberland Woodturners",
     "http://cumberlandwoodturners.com/",
     "Tennessee area club"),
    ("Other Club Websites", "San Diego Woodturners",
     "http://www.sdwt.org/",
     "California-based woodturning club"),
    ("Other Club Websites", "Tri State Woodturners",
     "http://www.tristatewoodturners.com/",
     "Multi-state regional club"),
    ("Other Club Websites", "Woodturners of North Texas",
     "http://www.woodturnersofnorthtexas.org/",
     "Texas-based woodturning club"),
]


def seed():
    db = SessionLocal()
    try:
        added = 0
        for category, title, url, description in RESOURCES:
            exists = (
                db.query(Resource)
                .filter(Resource.category == category, Resource.title == title)
                .first()
            )
            if not exists:
                db.add(Resource(
                    category=category,
                    title=title,
                    url=url,
                    description=description,
                    sort_order=0,
                    active=True,
                ))
                added += 1
        db.commit()
        print(f"✓ Seeded {added} resources ({len(RESOURCES) - added} already present)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
