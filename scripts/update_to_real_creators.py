"""Replace all fake test prospects with real creators across all platforms."""

import json
import psycopg2
import psycopg2.extras

psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
psycopg2.extensions.register_adapter(list, psycopg2.extras.Json)

DB_URL = "postgresql://bencamara@localhost:5433/kliq_growth_engine"

# ─── REAL CREATOR DATA ───

UPDATES = [
    # ══════════════════════════════════════════════════
    # YOUTUBE — replace 7 fake ones
    # ══════════════════════════════════════════════════
    {
        "id": 1,
        "name": "Chloe Ting",
        "first_name": "Chloe",
        "last_name": "Ting",
        "bio": "Free workout programs, HIIT challenges, and body sculpting routines. Known for viral 2-week shred challenges with millions of participants worldwide.",
        "primary_platform_id": "ChloeTing",
        "primary_platform_url": "https://www.youtube.com/@ChloeTing",
        "website_url": "https://www.chloeting.com",
        "social_links": {
            "instagram": "https://www.instagram.com/chloe_t/",
            "tiktok": "https://www.tiktok.com/@chloe_t",
            "youtube": "https://www.youtube.com/@ChloeTing"
        },
        "niche_tags": ["hiit", "home workouts", "body sculpting", "weight loss"],
        "location": "New York, USA",
        "follower_count": 2500000,
        "subscriber_count": 26000000,
        "brand_colors": ["#FF6B9D", "#C44569", "#FFC1CC"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/44.jpg",
    },
    {
        "id": 2,
        "name": "Joe Wicks",
        "first_name": "Joe",
        "last_name": "Wicks",
        "bio": "The Body Coach. HIIT workouts, Lean in 15 nutrition, and PE with Joe classes. Helped millions stay active during lockdown with free daily workouts.",
        "primary_platform_id": "TheBodyCoachTV",
        "primary_platform_url": "https://www.youtube.com/@TheBodyCoachTV",
        "website_url": "https://www.thebodycoach.com",
        "social_links": {
            "instagram": "https://www.instagram.com/thebodycoach/",
            "tiktok": "https://www.tiktok.com/@thebodycoach",
            "twitter": "https://x.com/thebodycoach",
            "youtube": "https://www.youtube.com/@TheBodyCoachTV"
        },
        "niche_tags": ["hiit", "nutrition", "home fitness", "lean in 15"],
        "location": "Surrey, England, UK",
        "follower_count": 4800000,
        "subscriber_count": 2900000,
        "brand_colors": ["#00C853", "#1B5E20", "#FFC107"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/32.jpg",
    },
    {
        "id": 3,
        "name": "Simeon Panda",
        "first_name": "Simeon",
        "last_name": "Panda",
        "bio": "Natural bodybuilder, fitness entrepreneur, and founder of Just Lift apparel. Sharing workout tutorials, gym vlogs, and physique transformation content.",
        "primary_platform_id": "SimeonPanda",
        "primary_platform_url": "https://www.youtube.com/@SimeonPanda",
        "website_url": "https://www.simeonpanda.com",
        "social_links": {
            "instagram": "https://www.instagram.com/simeonpanda/",
            "tiktok": "https://www.tiktok.com/@simeon_panda",
            "twitter": "https://x.com/SimeonPanda",
            "youtube": "https://www.youtube.com/@SimeonPanda"
        },
        "niche_tags": ["natural bodybuilding", "strength training", "physique"],
        "location": "Los Angeles, USA",
        "follower_count": 8000000,
        "subscriber_count": 2800000,
        "brand_colors": ["#212121", "#FF5722", "#FFFFFF"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/75.jpg",
    },
    {
        "id": 5,
        "name": "growwithjo",
        "first_name": "Johanna",
        "last_name": "Devries",
        "bio": "Fun indoor walking workouts and beginner-friendly cardio routines. Making fitness accessible with walking-based HIIT that anyone can do at home.",
        "primary_platform_id": "growwithjo",
        "primary_platform_url": "https://www.youtube.com/@growwithjo",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/growwithjo/",
            "tiktok": "https://www.tiktok.com/@growwithjo",
            "youtube": "https://www.youtube.com/@growwithjo"
        },
        "niche_tags": ["walking workouts", "home cardio", "beginner fitness"],
        "location": "Miami, Florida, USA",
        "follower_count": 1100000,
        "subscriber_count": 7900000,
        "brand_colors": ["#E91E63", "#F48FB1", "#880E4F"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/55.jpg",
    },
    {
        "id": 7,
        "name": "Sydney Cummings Houdyshell",
        "first_name": "Sydney",
        "last_name": "Cummings",
        "bio": "Daily free full-length strength training workouts. Structured monthly programs with dumbbells, HIIT, and mobility work. New workout every single day.",
        "primary_platform_id": "SydneyCummings",
        "primary_platform_url": "https://www.youtube.com/@SydneyCummings",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/sydneycummings_/",
            "tiktok": "https://www.tiktok.com/@sydneycummings_",
            "twitter": "https://x.com/sydneycummings_",
            "youtube": "https://www.youtube.com/@SydneyCummings"
        },
        "niche_tags": ["strength training", "daily workouts", "home fitness"],
        "location": "Charlotte, North Carolina, USA",
        "follower_count": 454000,
        "subscriber_count": 1600000,
        "brand_colors": ["#7B1FA2", "#E040FB", "#4A148C"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/60.jpg",
    },
    {
        "id": 10,
        "name": "Move With Nicole",
        "first_name": "Nicole",
        "last_name": "McPherson",
        "bio": "Pilates, yoga, and barre workouts for all levels. 200+ free classes blending mindful movement with effective training. Mat-based sessions you can do anywhere.",
        "primary_platform_id": "MoveWithNicole",
        "primary_platform_url": "https://www.youtube.com/@MoveWithNicole",
        "website_url": "https://movewithnicole.com.au",
        "social_links": {
            "instagram": "https://www.instagram.com/movewithnicole/",
            "tiktok": "https://www.tiktok.com/@movewithnicole",
            "youtube": "https://www.youtube.com/@MoveWithNicole"
        },
        "niche_tags": ["pilates", "yoga", "barre", "flexibility"],
        "location": "Koh Samui, Thailand",
        "follower_count": 576000,
        "subscriber_count": 5500000,
        "brand_colors": ["#BCAAA4", "#5D4037", "#EFEBE9"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/22.jpg",
    },
    {
        "id": 12,
        "name": "Tibo InShape",
        "first_name": "Thibaud",
        "last_name": "Delapart",
        "bio": "France's biggest fitness YouTuber. Bodybuilding tips, high-intensity challenges, and humor-driven fitness entertainment inspiring millions to train.",
        "primary_platform_id": "TiboInShape",
        "primary_platform_url": "https://www.youtube.com/@TiboInShape",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/tiboinshape/",
            "tiktok": "https://www.tiktok.com/@tiboinshape",
            "youtube": "https://www.youtube.com/@TiboInShape"
        },
        "niche_tags": ["bodybuilding", "fitness entertainment", "challenges"],
        "location": "Toulouse, France",
        "follower_count": 8500000,
        "subscriber_count": 27000000,
        "brand_colors": ["#F44336", "#212121", "#FFEB3B"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/40.jpg",
    },

    # ══════════════════════════════════════════════════
    # SKOOL — replace all 7
    # ══════════════════════════════════════════════════
    {
        "id": 4,
        "name": "Day by Day Wellness Club",
        "first_name": "Lena",
        "last_name": "Yeo",
        "bio": "A safe, supportive wellness community for anyone on their journey to becoming their best self. Founded by LenaLifts — fitness, wellness, and lifestyle for women.",
        "primary_platform_id": "day-by-day-family-4722",
        "primary_platform_url": "https://www.skool.com/day-by-day-family-4722/about",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/lenaliftsx/",
            "youtube": "https://www.youtube.com/@LenaLifts",
            "tiktok": "https://www.tiktok.com/@lenalifts"
        },
        "niche_tags": ["wellness", "fitness", "lifestyle", "women's health"],
        "location": "New York, USA",
        "follower_count": 312000,
        "subscriber_count": 61300,
        "brand_colors": ["#F8BBD0", "#E91E63", "#FCE4EC"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/15.jpg",
    },
    {
        "id": 9,
        "name": "FitGurl",
        "first_name": "Melissa",
        "last_name": "Alcantara",
        "bio": "Celebrity trainer (Kim Kardashian's PT), USA Today bestselling author of 'Fit Gurl', and creator of the ANUE fitness app. Empowering women through fitness.",
        "primary_platform_id": "fitgurl-community",
        "primary_platform_url": "https://www.skool.com/fitgurl-community/about",
        "website_url": "https://fitgurlmel.com",
        "social_links": {
            "instagram": "https://www.instagram.com/fitgurlmel/",
            "tiktok": "https://www.tiktok.com/@fitgurlmel"
        },
        "niche_tags": ["women's fitness", "body transformation", "celebrity training"],
        "location": "Los Angeles, California, USA",
        "follower_count": 1000000,
        "subscriber_count": 0,
        "brand_colors": ["#FF6F00", "#E65100", "#FFF3E0"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/48.jpg",
    },
    {
        "id": 27,
        "name": "Full-Time Fit Coach",
        "first_name": "Will",
        "last_name": "Girone",
        "bio": "Private community for online fitness coaches who want to sign high-ticket clients. 5 weekly coaching calls, 15 fitness business courses, and a peer community of 300+ coaches.",
        "primary_platform_id": "full-time-fit-coach",
        "primary_platform_url": "https://www.skool.com/full-time-fit-coach/about",
        "website_url": "https://fulltimefitcoach.com",
        "social_links": {
            "instagram": "https://www.instagram.com/willgirone/",
            "linkedin": "https://www.linkedin.com/in/willgirone"
        },
        "niche_tags": ["fitness business", "online coaching", "high-ticket sales"],
        "location": "USA",
        "follower_count": 93000,
        "subscriber_count": 326,
        "brand_colors": ["#1565C0", "#0D47A1", "#E3F2FD"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/25.jpg",
    },
    {
        "id": 32,
        "name": "Remote Fitness CEOs",
        "first_name": "Jemes",
        "last_name": "Sintel",
        "bio": "Helping personal trainers start profitable online fitness businesses so they stop trading time on the gym floor. Free $10K/Month Online Fitness Coach Checklist.",
        "primary_platform_id": "remote-fitness-ceos-3251",
        "primary_platform_url": "https://www.skool.com/remote-fitness-ceos-3251",
        "website_url": "https://remotefitnessceos.com",
        "social_links": {
            "instagram": "https://www.instagram.com/_kingfitness/"
        },
        "niche_tags": ["fitness business", "online personal training", "entrepreneurship"],
        "location": "USA",
        "follower_count": 153000,
        "subscriber_count": 451,
        "brand_colors": ["#4CAF50", "#1B5E20", "#E8F5E9"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/43.jpg",
    },
    {
        "id": 34,
        "name": "Endless Evolution w/ Duffin",
        "first_name": "Chris",
        "last_name": "Duffin",
        "bio": "World-record holding powerlifter and founder of Kabuki Strength. 1000+ indexed training videos, monthly eBooks, weekly live calls. The Mad Scientist of Strength.",
        "primary_platform_id": "endless-evolution-8560",
        "primary_platform_url": "https://www.skool.com/endless-evolution-8560/about",
        "website_url": "https://chrisduffin.com",
        "social_links": {
            "instagram": "https://www.instagram.com/mad_scientist_duffin/"
        },
        "niche_tags": ["powerlifting", "strength training", "human performance", "longevity"],
        "location": "Portland, Oregon, USA",
        "follower_count": 341000,
        "subscriber_count": 0,
        "brand_colors": ["#263238", "#B71C1C", "#ECEFF1"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/65.jpg",
    },
    {
        "id": 35,
        "name": "Youthspan Society",
        "first_name": "Siim",
        "last_name": "Land",
        "bio": "The #1 evidence-based anti-aging, longevity, and wellness community. Bestselling author with 8+ books on health optimization. Lower your biological age with science-backed strategies.",
        "primary_platform_id": "youthspan-society",
        "primary_platform_url": "https://www.skool.com/youthspan-society/about",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/siimland/",
            "youtube": "https://www.youtube.com/@SiimLand"
        },
        "niche_tags": ["anti-aging", "longevity", "biohacking", "wellness"],
        "location": "Chiang Mai, Thailand",
        "follower_count": 409000,
        "subscriber_count": 214000,
        "brand_colors": ["#00BCD4", "#006064", "#E0F7FA"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/19.jpg",
    },
    {
        "id": 36,
        "name": "Fitness Coaching Community",
        "first_name": "Jannis",
        "last_name": "Neumann",
        "bio": "German-language community for fitness coaches focused on the 100,000 EUR Coaching Model. Premium coaching basics, case studies, and customer acquisition strategies.",
        "primary_platform_id": "fitness-coaching-community",
        "primary_platform_url": "https://www.skool.com/fitness-coaching-community/about",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/jannis_neumann/"
        },
        "niche_tags": ["fitness business", "coaching", "german market"],
        "location": "Germany",
        "follower_count": 6400,
        "subscriber_count": 2200,
        "brand_colors": ["#FF9800", "#E65100", "#FFF3E0"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/36.jpg",
    },

    # ══════════════════════════════════════════════════
    # PATREON — replace all 5
    # ══════════════════════════════════════════════════
    {
        "id": 6,
        "name": "HASfit",
        "first_name": "Joshua",
        "last_name": "Kozak",
        "bio": "Coach Kozak — ISSA-certified trainer with 15+ years experience. Named Google's Top 10 Trainers on YouTube. Free full-length workouts, monthly calendars, and premium 1-on-1 coaching.",
        "primary_platform_id": "hasfit",
        "primary_platform_url": "https://www.patreon.com/hasfit",
        "website_url": "https://hasfit.com",
        "social_links": {
            "instagram": "https://www.instagram.com/hasfit_official/",
            "youtube": "https://www.youtube.com/@HASfit"
        },
        "niche_tags": ["home fitness", "workout programs", "personal training"],
        "location": "San Antonio, Texas, USA",
        "follower_count": 94000,
        "subscriber_count": 2200000,
        "brand_colors": ["#2196F3", "#0D47A1", "#E3F2FD"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/52.jpg",
    },
    {
        "id": 33,
        "name": "Fitness with PJ",
        "first_name": "PJ",
        "last_name": "Wren",
        "bio": "Results-based workout videos for women over 40, 50, and 60+. Certified personal trainer since 1994 with 30+ years experience. Functional fitness and building confidence.",
        "primary_platform_id": "fitnesswithpj",
        "primary_platform_url": "https://www.patreon.com/fitnesswithpj",
        "website_url": "https://www.fitnesswithpj.com",
        "social_links": {
            "instagram": "https://www.instagram.com/fitnesswithpj/",
            "youtube": "https://www.youtube.com/@FitnesswithPJ",
            "twitter": "https://x.com/fitnesswithpj"
        },
        "niche_tags": ["women over 40", "functional fitness", "low impact"],
        "location": "UK",
        "follower_count": 16000,
        "subscriber_count": 147000,
        "brand_colors": ["#AB47BC", "#6A1B9A", "#F3E5F5"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/60.jpg",
    },
    {
        "id": 40,
        "name": "Caroline Jordan Fitness",
        "first_name": "Caroline",
        "last_name": "Jordan",
        "bio": "The #1 source of injury-friendly fitness on the internet. 500+ videos using movement as medicine for mental and physical wellbeing. 20+ years coaching experience.",
        "primary_platform_id": "carolinejordanfitness",
        "primary_platform_url": "https://www.patreon.com/carolinejordanfitness",
        "website_url": "https://carolinejordanfitness.com",
        "social_links": {
            "instagram": "https://www.instagram.com/carolinejordanfitness/",
            "youtube": "https://www.youtube.com/@carolinejordan",
            "twitter": "https://x.com/carolinefitness"
        },
        "niche_tags": ["injury-friendly fitness", "movement as medicine", "wellness"],
        "location": "San Diego, California, USA",
        "follower_count": 17000,
        "subscriber_count": 750000,
        "brand_colors": ["#26C6DA", "#00838F", "#E0F7FA"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/82.jpg",
    },
    {
        "id": 41,
        "name": "GAINS",
        "first_name": "Adam",
        "last_name": "Fisher",
        "bio": "Body-positive strength training coaching. 250+ remote clients since 2012. Westside Barbell intern, Stronger By Science contributor. Powerlifting, bodybuilding, self-improvement.",
        "primary_platform_id": "gains",
        "primary_platform_url": "https://www.patreon.com/gains",
        "website_url": "https://www.gains.af",
        "social_links": {
            "instagram": "https://www.instagram.com/gains_strength/"
        },
        "niche_tags": ["strength training", "powerlifting", "bodybuilding", "body-positive"],
        "location": "United Kingdom",
        "follower_count": 2850,
        "subscriber_count": 0,
        "brand_colors": ["#424242", "#FF5722", "#FAFAFA"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/30.jpg",
    },
    {
        "id": 42,
        "name": "Flex Formation Fitness",
        "first_name": None,
        "last_name": None,
        "bio": "1000+ home workout videos, nutrition plans, recipes, fitness calculators and tracking logs. 80% nutrition, 20% exercise. Affordable, accessible home-based fitness.",
        "primary_platform_id": "Flexformation",
        "primary_platform_url": "https://www.patreon.com/Flexformation",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/flexfit352/"
        },
        "niche_tags": ["home workouts", "nutrition", "budget fitness"],
        "location": "UK",
        "follower_count": 0,
        "subscriber_count": 0,
        "brand_colors": ["#43A047", "#1B5E20", "#C8E6C9"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/48.jpg",
    },

    # ══════════════════════════════════════════════════
    # WEBSITE — replace all 5
    # ══════════════════════════════════════════════════
    {
        "id": 8,
        "name": "Scott Laidler Coaching",
        "first_name": "Scott",
        "last_name": "Laidler",
        "bio": "Ranked No.1 Online PT by the Institute of Personal Trainers. Sustainable fitness for busy professionals in law, finance, tech, and medicine. Serving clients in 54 countries.",
        "primary_platform_id": "scottlaidler",
        "primary_platform_url": "https://scottlaidler.com",
        "website_url": "https://scottlaidler.com",
        "social_links": {
            "instagram": "https://www.instagram.com/scottlaidlercoaching/",
            "linkedin": "https://www.linkedin.com/in/scottlaidler/"
        },
        "niche_tags": ["online personal training", "busy professionals", "sustainable fitness"],
        "location": "United Kingdom",
        "follower_count": 7024,
        "subscriber_count": 0,
        "brand_colors": ["#1A237E", "#283593", "#E8EAF6"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/80.jpg",
    },
    {
        "id": 11,
        "name": "FITBODY by Julie Lohre",
        "first_name": "Julie",
        "last_name": "Lohre",
        "bio": "IFBB Fitness Pro, CPT, Certified Nutrition Specialist. Pioneer of online personal training since 2002. Coached 2000+ women. American Ninja Warrior competitor.",
        "primary_platform_id": "julielohre",
        "primary_platform_url": "https://julielohre.com",
        "website_url": "https://julielohre.com",
        "social_links": {
            "instagram": "https://www.instagram.com/julielohre/"
        },
        "niche_tags": ["women's fitness", "online coaching", "nutrition", "over 40"],
        "location": "Ohio, USA",
        "follower_count": 5752,
        "subscriber_count": 0,
        "brand_colors": ["#D81B60", "#880E4F", "#FCE4EC"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/42.jpg",
    },
    {
        "id": 37,
        "name": "Yoga with Kassandra",
        "first_name": "Kassandra",
        "last_name": "Reinhardt",
        "bio": "Yin Yoga and Vinyasa Flow. 750+ videos on membership platform. Published author of 'Yin Yoga: Stretch the Mindful Way' (Penguin). Yoga Alliance certified teacher trainer.",
        "primary_platform_id": "yogawithkassandra",
        "primary_platform_url": "https://www.yogawithkassandra.com",
        "website_url": "https://www.yogawithkassandra.com",
        "social_links": {
            "instagram": "https://www.instagram.com/yoga_with_kassandra/",
            "youtube": "https://www.youtube.com/@yogawithkassandra"
        },
        "niche_tags": ["yin yoga", "vinyasa", "yoga teacher training", "mindfulness"],
        "location": "Ottawa, Ontario, Canada",
        "follower_count": 174000,
        "subscriber_count": 3000000,
        "brand_colors": ["#8D6E63", "#4E342E", "#EFEBE9"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/25.jpg",
    },
    {
        "id": 38,
        "name": "Ben Greenfield Life",
        "first_name": "Ben",
        "last_name": "Greenfield",
        "bio": "Ex-bodybuilder, Ironman triathlete, and human performance consultant. NYT bestselling author of 'Boundless'. Biohacking, longevity, and optimized fitness for high performers.",
        "primary_platform_id": "bengreenfield",
        "primary_platform_url": "https://bengreenfieldlife.com",
        "website_url": "https://bengreenfieldlife.com",
        "social_links": {
            "instagram": "https://www.instagram.com/bengaborasong/",
            "youtube": "https://www.youtube.com/@BenGreenfieldLife",
            "twitter": "https://x.com/bengreenfield"
        },
        "niche_tags": ["biohacking", "longevity", "performance optimization", "nutrition"],
        "location": "Spokane, Washington, USA",
        "follower_count": 600000,
        "subscriber_count": 500000,
        "brand_colors": ["#2E7D32", "#1B5E20", "#E8F5E9"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/12.jpg",
    },
    {
        "id": 39,
        "name": "Jillian Michaels",
        "first_name": "Jillian",
        "last_name": "Michaels",
        "bio": "America's most famous fitness trainer. Former Biggest Loser coach. The Jillian Michaels Fitness App with personalized workouts, meal plans, and 800+ exercises.",
        "primary_platform_id": "jillianmichaels",
        "primary_platform_url": "https://www.jillianmichaels.com",
        "website_url": "https://www.jillianmichaels.com",
        "social_links": {
            "instagram": "https://www.instagram.com/jillianmichaels/",
            "youtube": "https://www.youtube.com/@JillianMichaels",
            "twitter": "https://x.com/JillianMichaels"
        },
        "niche_tags": ["weight loss", "personal training", "fitness app", "nutrition"],
        "location": "Miami, Florida, USA",
        "follower_count": 7100000,
        "subscriber_count": 1200000,
        "brand_colors": ["#F44336", "#B71C1C", "#FFEBEE"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/33.jpg",
    },

    # ══════════════════════════════════════════════════
    # ONLYFANS — replace all 13
    # ══════════════════════════════════════════════════
    {
        "id": 43,
        "name": "Jem Wolfie",
        "first_name": "Jem",
        "last_name": "Wolfie",
        "bio": "Australian fitness coach, chef, and entrepreneur. Exclusive workout videos, personal fitness tutorials, meal-prep guides, and lifestyle content. Top non-adult earner on OnlyFans.",
        "primary_platform_id": "jemwolfie",
        "primary_platform_url": "https://onlyfans.com/jemwolfie",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/jemwolfie/"
        },
        "niche_tags": ["fitness coaching", "meal prep", "lifestyle"],
        "location": "Perth, Australia",
        "follower_count": 2700000,
        "subscriber_count": 400000,
        "brand_colors": ["#FF6F00", "#E65100", "#FFF3E0"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/3.jpg",
    },
    {
        "id": 44,
        "name": "Ana Cheri",
        "first_name": "Ana",
        "last_name": "Cheri",
        "bio": "NPC bodybuilding champion, gym owner (Be More Athletics), CEO of Cheri Fit Activewear. Published 3 books on health and fitness. Free OnlyFans with SFW workout content via OFTV.",
        "primary_platform_id": "anacheri",
        "primary_platform_url": "https://onlyfans.com/anacheri",
        "website_url": "https://www.cherifitactivewear.com",
        "social_links": {
            "instagram": "https://www.instagram.com/anacheri/",
            "youtube": "https://www.youtube.com/@AnaCheriFit"
        },
        "niche_tags": ["bodybuilding", "fitness programs", "activewear"],
        "location": "Santa Ana, California, USA",
        "follower_count": 12000000,
        "subscriber_count": 0,
        "brand_colors": ["#E91E63", "#880E4F", "#FCE4EC"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/48.jpg",
    },
    {
        "id": 45,
        "name": "Mike Chabot Fitness",
        "first_name": "Mike",
        "last_name": "Chabot",
        "bio": "Personal trainer, neuroengineer, and abundance coach. Exclusive recipes, workout plans, and fitness coaching. 6M+ combined followers across platforms.",
        "primary_platform_id": "mikechabotfitness",
        "primary_platform_url": "https://onlyfans.com/mikechabotfitness",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/mikechabotfitness/",
            "twitter": "https://x.com/officialbigman6"
        },
        "niche_tags": ["personal training", "nutrition", "workout plans"],
        "location": "USA",
        "follower_count": 1300000,
        "subscriber_count": 0,
        "brand_colors": ["#37474F", "#263238", "#ECEFF1"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/8.jpg",
    },
    {
        "id": 49,
        "name": "Daisy Keech",
        "first_name": "Daisy",
        "last_name": "Keech",
        "bio": "Fitness influencer and creator of the Keech Peach brand. Specializing in glute development and total body conditioning. 17M+ combined followers across platforms.",
        "primary_platform_id": "daisykeech",
        "primary_platform_url": "https://onlyfans.com/daisykeech",
        "website_url": "https://keechpeach.com",
        "social_links": {
            "instagram": "https://www.instagram.com/daisykeech/",
            "tiktok": "https://www.tiktok.com/@daisykeech",
            "twitter": "https://x.com/DaisyKeech"
        },
        "niche_tags": ["glute training", "body conditioning", "lifestyle"],
        "location": "Los Angeles, California, USA",
        "follower_count": 5400000,
        "subscriber_count": 0,
        "brand_colors": ["#F48FB1", "#EC407A", "#FFF0F5"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/57.jpg",
    },
    {
        "id": 50,
        "name": "Eva Andressa",
        "first_name": "Eva",
        "last_name": "Andressa",
        "bio": "Brazilian fitness model and competitive bodybuilder. Won NABBA Lobo Bravo Cup 2005. IFBB Body Fitness champion. Body sculpting, toning techniques, and workout routines.",
        "primary_platform_id": "eva_andressa",
        "primary_platform_url": "https://onlyfans.com/eva_andressa",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/eva_andressa/",
            "twitter": "https://x.com/EvaAndressaOf"
        },
        "niche_tags": ["bodybuilding", "body sculpting", "fitness modeling"],
        "location": "Brazil",
        "follower_count": 6000000,
        "subscriber_count": 0,
        "brand_colors": ["#FF7043", "#BF360C", "#FBE9E7"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/76.jpg",
    },
    {
        "id": 51,
        "name": "Anllela Sagra",
        "first_name": "Anllela",
        "last_name": "Sagra",
        "bio": "Colombian fitness model and personal trainer. Creator of the Anllela Sagra Fitness app. Transformation programs with carb cycling, weight training, and ab circuits.",
        "primary_platform_id": "anllelasagra",
        "primary_platform_url": "https://onlyfans.com/anllelasagra",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/anllela_sagra/",
            "twitter": "https://x.com/anllelasagraa"
        },
        "niche_tags": ["fitness modeling", "personal training", "body transformation"],
        "location": "Medellin, Colombia",
        "follower_count": 14000000,
        "subscriber_count": 0,
        "brand_colors": ["#7C4DFF", "#4527A0", "#EDE7F6"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/19.jpg",
    },
    {
        "id": 52,
        "name": "Danielle Cooper",
        "first_name": "Danielle",
        "last_name": "Cooper",
        "bio": "Ms Booty Gains — transformative glute workouts, weightlifting, proper nutrition, and consistent dedication. Fitness model, TikTok influencer, and OnlyFans creator.",
        "primary_platform_id": "danicoopps",
        "primary_platform_url": "https://onlyfans.com/danicoopps",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/danicooppss/",
            "tiktok": "https://www.tiktok.com/@danicoopps"
        },
        "niche_tags": ["glute training", "weightlifting", "booty building"],
        "location": "New Jersey, USA",
        "follower_count": 1800000,
        "subscriber_count": 0,
        "brand_colors": ["#D32F2F", "#B71C1C", "#FFEBEE"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/88.jpg",
    },
    {
        "id": 53,
        "name": "Mel G Fitness",
        "first_name": "Melissa",
        "last_name": "Gonzalez",
        "bio": "CEO of Fit Esteem — training and lifestyle platform empowering women through fitness. Train Like Mel G workout series for full-body training and glute sculpting.",
        "primary_platform_id": "melgfit",
        "primary_platform_url": "https://onlyfans.com/melgfit",
        "website_url": "https://melgofficial.com",
        "social_links": {
            "instagram": "https://www.instagram.com/melgfit/",
            "tiktok": "https://www.tiktok.com/@melgfit",
            "twitter": "https://x.com/melgfit"
        },
        "niche_tags": ["women's empowerment", "glute sculpting", "full-body fitness"],
        "location": "USA",
        "follower_count": 1000000,
        "subscriber_count": 0,
        "brand_colors": ["#CE93D8", "#6A1B9A", "#F3E5F5"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/32.jpg",
    },
    {
        "id": 54,
        "name": "Kiera Bernier",
        "first_name": "Kiera",
        "last_name": "Bernier",
        "bio": "At-home equipment-free fitness content. Former volleyball player and dancer. Bite-sized instructional workout videos using minimal equipment. Featured on OFTV.",
        "primary_platform_id": "kierabernier",
        "primary_platform_url": "https://onlyfans.com/kierabernier",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/kiera.bernier/",
            "tiktok": "https://www.tiktok.com/@kierabernier",
            "twitter": "https://x.com/kiera_bernier"
        },
        "niche_tags": ["home fitness", "equipment-free", "bodyweight training"],
        "location": "Amsterdam, Netherlands",
        "follower_count": 32000,
        "subscriber_count": 0,
        "brand_colors": ["#4DB6AC", "#00695C", "#E0F2F1"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/66.jpg",
    },
    {
        "id": 55,
        "name": "Yoga with Taz",
        "first_name": "Taz",
        "last_name": None,
        "bio": "Yogi and wellness expert. Yoga routines, guided meditations, and motivational content. Hosts Wellness Wednesday live yoga sessions. Beach Yoga and Nighttime Bed Yoga on OFTV.",
        "primary_platform_id": "onlytaz",
        "primary_platform_url": "https://onlyfans.com/onlytaz",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/_yogawithtaz_/",
            "twitter": "https://x.com/yogawithtaz"
        },
        "niche_tags": ["yoga", "meditation", "wellness", "mindfulness"],
        "location": None,
        "follower_count": 0,
        "subscriber_count": 0,
        "brand_colors": ["#81C784", "#2E7D32", "#E8F5E9"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/45.jpg",
    },
    {
        "id": 56,
        "name": "Holly Barker Fitness",
        "first_name": "Holly",
        "last_name": "Barker",
        "bio": "Mother of 5, NASM-certified trainer, NPC bikini athlete. Opened 5 gyms and a spa. Hosts The Fitness Gurls Podcast. Fitness business mentorship and strength programs.",
        "primary_platform_id": "hollybarker",
        "primary_platform_url": "https://onlyfans.com/hollybarker",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/hollybarkerofficial/",
            "tiktok": "https://www.tiktok.com/@hollybarkerofficial",
            "twitter": "https://x.com/hollsbarks"
        },
        "niche_tags": ["personal training", "NPC bikini", "fitness mentorship"],
        "location": "USA",
        "follower_count": 1000000,
        "subscriber_count": 0,
        "brand_colors": ["#FF8A65", "#BF360C", "#FBE9E7"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/8.jpg",
    },
    {
        "id": 57,
        "name": "Alex Mara",
        "first_name": "Alex",
        "last_name": "Mara",
        "bio": "Personal trainer, developer, and food photographer based in Miami. Fitness techniques, lifestyle advice, and nutrition tips. Partners with Paragon Fitwear.",
        "primary_platform_id": "alexxmara",
        "primary_platform_url": "https://onlyfans.com/alexxmara",
        "website_url": None,
        "social_links": {
            "instagram": "https://www.instagram.com/alexxmara/",
            "tiktok": "https://www.tiktok.com/@alexxmara",
            "twitter": "https://x.com/alexxmara"
        },
        "niche_tags": ["personal training", "nutrition", "food photography"],
        "location": "Miami, Florida, USA",
        "follower_count": 61000,
        "subscriber_count": 0,
        "brand_colors": ["#546E7A", "#263238", "#ECEFF1"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/45.jpg",
    },
    {
        "id": 58,
        "name": "Body by Blair",
        "first_name": "Autumn",
        "last_name": "Blair",
        "bio": "Bikini model, certified PT, yoga teacher. IFBB competitor — 1st place Northern Classic Open Bikini. Tone-and-sculpt guides, Blair's Booty Blast, macro meal plans, and weekly yoga.",
        "primary_platform_id": "bodybyblair",
        "primary_platform_url": "https://onlyfans.com/bodybyblair",
        "website_url": "https://bodybyblair.com",
        "social_links": {
            "instagram": "https://www.instagram.com/autumnblair_xo/",
            "youtube": "https://www.youtube.com/@autumnblairxo",
            "tiktok": "https://www.tiktok.com/@autumnblairxo",
            "twitter": "https://x.com/AutumnBlair_xo"
        },
        "niche_tags": ["bikini bodybuilding", "yoga", "online coaching", "meal plans"],
        "location": "Miami, Florida, USA",
        "follower_count": 575000,
        "subscriber_count": 66000,
        "brand_colors": ["#EC407A", "#AD1457", "#FCE4EC"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/91.jpg",
    },

    # ══════════════════════════════════════════════════
    # KAJABI — replace all 3
    # ══════════════════════════════════════════════════
    {
        "id": 46,
        "name": "Barre Definition",
        "first_name": "Jacquelyn",
        "last_name": "Umof",
        "bio": "Former Laker Girl and professional dancer with 20+ years experience. 800+ premium Barre and Pilates classes. Heal My Gut wellness program. 7-figure Kajabi business.",
        "primary_platform_id": "barredefinition",
        "primary_platform_url": "https://barredefinition.com",
        "website_url": "https://barredefinition.com",
        "social_links": {
            "instagram": "https://www.instagram.com/actionjacquelyn/",
            "youtube": "https://www.youtube.com/@actionjacquelyn"
        },
        "niche_tags": ["barre", "pilates", "dance fitness", "gut health"],
        "location": "San Diego, California, USA",
        "follower_count": 629000,
        "subscriber_count": 271000,
        "brand_colors": ["#F48FB1", "#C2185B", "#FCE4EC"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/40.jpg",
    },
    {
        "id": 47,
        "name": "Knocked-Up Fitness",
        "first_name": "Erica",
        "last_name": "Ziel",
        "bio": "Pre/postnatal fitness expert with 20+ years in Pilates. Core Rehab Program, prenatal workouts, and pelvic floor health. NASM, STOTT PILATES, and PMA certified.",
        "primary_platform_id": "ericaziel",
        "primary_platform_url": "https://www.ericaziel.com",
        "website_url": "https://www.ericaziel.com",
        "social_links": {
            "instagram": "https://www.instagram.com/ericaziel/",
            "youtube": "https://www.youtube.com/@EricaZiel",
            "twitter": "https://x.com/ericaziel"
        },
        "niche_tags": ["prenatal fitness", "postnatal", "pilates", "core rehab", "pelvic floor"],
        "location": "Ankeny, Iowa, USA",
        "follower_count": 20000,
        "subscriber_count": 5000,
        "brand_colors": ["#AB47BC", "#6A1B9A", "#F3E5F5"],
        "profile_image_url": "https://randomuser.me/api/portraits/women/53.jpg",
    },
    {
        "id": 48,
        "name": "Grow Young Fitness",
        "first_name": "Deron",
        "last_name": "Buboltz",
        "bio": "Senior fitness specialist — 300+ low-impact chair-based workout videos. BS in Exercise Science, Arthritis Foundation certified. Serving seniors in their 60s-80s. BBB accredited.",
        "primary_platform_id": "growyoungfitness",
        "primary_platform_url": "https://www.growyoungfitness.com",
        "website_url": "https://www.growyoungfitness.com",
        "social_links": {
            "instagram": "https://www.instagram.com/growyoungfitness/",
            "youtube": "https://www.youtube.com/@GrowYoungFitness",
            "tiktok": "https://www.tiktok.com/@growyoungfitness",
            "twitter": "https://x.com/GrowYoungFit"
        },
        "niche_tags": ["senior fitness", "chair exercises", "low-impact", "arthritis-friendly"],
        "location": "Lahaina, Hawaii, USA",
        "follower_count": 914000,
        "subscriber_count": 327000,
        "brand_colors": ["#66BB6A", "#2E7D32", "#E8F5E9"],
        "profile_image_url": "https://randomuser.me/api/portraits/men/35.jpg",
    },
]


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    updated = 0
    for c in UPDATES:
        cur.execute("""
            UPDATE prospects SET
                name = %s,
                first_name = %s,
                last_name = %s,
                bio = %s,
                primary_platform_id = %s,
                primary_platform_url = %s,
                website_url = %s,
                social_links = %s,
                niche_tags = %s,
                location = %s,
                follower_count = %s,
                subscriber_count = %s,
                brand_colors = %s,
                profile_image_url = %s,
                email = NULL
            WHERE id = %s
        """, (
            c["name"], c["first_name"], c["last_name"], c["bio"],
            c["primary_platform_id"], c["primary_platform_url"],
            c["website_url"], c["social_links"], c["niche_tags"],
            c["location"], c["follower_count"], c["subscriber_count"],
            c["brand_colors"], c["profile_image_url"], c["id"]
        ))
        updated += cur.rowcount

        # Update generated_content bio to match
        bio_json = json.dumps({
            "store_name": c["name"],
            "short_bio": c["bio"],
            "niche": c["niche_tags"][0] if c["niche_tags"] else ""
        })
        cur.execute("""
            UPDATE generated_content
            SET body = %s, title = %s
            WHERE prospect_id = %s AND content_type = 'bio'
        """, (bio_json, f"{c['name']} Bio", c["id"]))

        # Update generated_content colors to match brand
        if c["brand_colors"]:
            color_json = json.dumps({
                "primary": c["brand_colors"][0],
                "secondary": c["brand_colors"][1] if len(c["brand_colors"]) > 1 else c["brand_colors"][0],
                "hero_bg": c["brand_colors"][1] if len(c["brand_colors"]) > 1 else c["brand_colors"][0],
                "accent": c["brand_colors"][2] if len(c["brand_colors"]) > 2 else c["brand_colors"][0]
            })
            cur.execute("""
                UPDATE generated_content
                SET body = %s
                WHERE prospect_id = %s AND content_type = 'colors'
            """, (color_json, c["id"]))

    conn.commit()
    print(f"Updated {updated} prospects with real creator data")

    # Verify
    cur.execute("""
        SELECT primary_platform, COUNT(*), STRING_AGG(name, ', ' ORDER BY id)
        FROM prospects
        WHERE id != 100
        GROUP BY primary_platform
        ORDER BY primary_platform
    """)
    for row in cur.fetchall():
        print(f"\n  {row[0]} ({row[1]}):")
        for name in row[2].split(", "):
            print(f"    - {name}")

    conn.close()


if __name__ == "__main__":
    main()
