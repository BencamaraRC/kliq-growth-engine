"""Seed test coaches across 5 platforms: Skool, Website, Patreon, OnlyFans, Kajabi.

3 coaches per platform = 15 total. Each has scraped content and pricing tiers.

Usage:
    cd kliq-growth-engine
    python scripts/seed_platform_test_data.py
"""

import json

import psycopg2

DB_URL = "postgresql://bencamara@localhost:5433/kliq_growth_engine"

# --- Test Data ---

COACHES = [
    # === SKOOL (3) ===
    {
        "name": "Marcus Rivera Fitness",
        "email": "marcus@riverafitness.com",
        "first_name": "Marcus",
        "last_name": "Rivera",
        "primary_platform": "SKOOL",
        "primary_platform_id": "rivera-fitness-elite",
        "primary_platform_url": "https://www.skool.com/rivera-fitness-elite",
        "bio": "Former D1 athlete turned strength coach. Building the #1 fitness community on Skool. Specializing in powerlifting, nutrition coaching, and body recomposition. 10+ years training experience.",
        "website_url": "https://riverafitness.com",
        "social_links": {
            "instagram": "@marcusriverafit",
            "youtube": "@RiveraFitness",
            "tiktok": "@marcusrivera",
        },
        "niche_tags": ["strength", "nutrition", "coaching", "powerlifting"],
        "location": "Houston, TX",
        "follower_count": 28500,
        "subscriber_count": 4200,
        "content_count": 156,
        "brand_colors": ["#E63946", "#1D3557", "#F1FAEE"],
        "status": "SCRAPED",
        "content": [
            {
                "type": "post",
                "title": "Progressive Overload: The Only Rule That Matters",
                "body": "Stop program hopping. Here's a 12-week progressive overload template that actually works...",
            },
            {
                "type": "post",
                "title": "My Top 5 Meals for Gaining Muscle Without Getting Fat",
                "body": "Meal prep Sunday! Here are the exact meals I eat to stay at 12% body fat while gaining strength...",
            },
        ],
        "pricing": [
            {
                "tier": "Community (Free)",
                "price": 0,
                "interval": "month",
                "members": 3200,
                "benefits": ["Weekly Q&A", "Exercise library", "Community forum"],
            },
            {
                "tier": "Elite Training",
                "price": 49.99,
                "interval": "month",
                "members": 980,
                "benefits": [
                    "Custom programs",
                    "Form checks",
                    "1-on-1 coaching calls",
                    "Nutrition templates",
                ],
            },
        ],
    },
    {
        "name": "ZenFlow Yoga Collective",
        "email": "luna@zenflow.co",
        "first_name": "Luna",
        "last_name": "Patel",
        "primary_platform": "SKOOL",
        "primary_platform_id": "zenflow-yoga",
        "primary_platform_url": "https://www.skool.com/zenflow-yoga",
        "bio": "Yoga teacher training & mindfulness community. RYT-500 certified. Teaching vinyasa, yin, and meditation for busy professionals. Join 2000+ students on their wellness journey.",
        "website_url": "https://zenflow.co",
        "social_links": {"instagram": "@zenflowluna", "youtube": "@ZenFlowYoga"},
        "niche_tags": ["yoga", "wellness", "meditation", "coaching"],
        "location": "Austin, TX",
        "follower_count": 15200,
        "subscriber_count": 2100,
        "content_count": 89,
        "brand_colors": ["#6B705C", "#DDBEA9", "#FFE8D6"],
        "status": "CONTENT_GENERATED",
        "content": [
            {
                "type": "post",
                "title": "Morning Vinyasa Flow (30 min)",
                "body": "Start your day with this gentle flow sequence designed for all levels...",
            },
            {
                "type": "post",
                "title": "Breathwork for Anxiety: 3 Techniques That Work",
                "body": "When anxiety hits, try these pranayama techniques I teach in my teacher training...",
            },
        ],
        "pricing": [
            {
                "tier": "Free Community",
                "price": 0,
                "interval": "month",
                "members": 1800,
                "benefits": ["Weekly live class", "Community support"],
            },
            {
                "tier": "Teacher Training",
                "price": 79.00,
                "interval": "month",
                "members": 310,
                "benefits": [
                    "Full YTT curriculum",
                    "Mentorship",
                    "Certification prep",
                    "Live workshops",
                ],
            },
        ],
    },
    {
        "name": "ShredLab Community",
        "email": "coach@shredlab.io",
        "first_name": "Jake",
        "last_name": "Thompson",
        "primary_platform": "SKOOL",
        "primary_platform_id": "shredlab-fitness",
        "primary_platform_url": "https://www.skool.com/shredlab-fitness",
        "bio": "Fat loss & body transformation community. NASM certified. I help busy dads lose 30+ lbs in 90 days without giving up beer. Real results, real people.",
        "social_links": {"instagram": "@shredlabcoach", "tiktok": "@shredlab"},
        "niche_tags": ["weight_loss", "fitness", "nutrition", "coaching"],
        "location": "Denver, CO",
        "follower_count": 9800,
        "subscriber_count": 1450,
        "content_count": 67,
        "brand_colors": ["#FF6B35", "#004E89", "#F5F5F5"],
        "status": "STORE_CREATED",
        "content": [
            {
                "type": "post",
                "title": "The Beer Belly Protocol: Week 1",
                "body": "You don't need to quit drinking to lose weight. Here's how I structure nutrition around social life...",
            },
        ],
        "pricing": [
            {
                "tier": "Free Shredders",
                "price": 0,
                "interval": "month",
                "members": 1100,
                "benefits": ["Workout of the day", "Recipe database"],
            },
            {
                "tier": "90-Day Shred",
                "price": 97.00,
                "interval": "month",
                "members": 350,
                "benefits": [
                    "Custom meal plan",
                    "Weekly check-ins",
                    "Video coaching",
                    "Private chat",
                ],
            },
        ],
    },
    # === WEBSITE (3) ===
    {
        "name": "Iron Mind Performance",
        "email": "alex@ironmindperformance.com",
        "first_name": "Alex",
        "last_name": "Chen",
        "primary_platform": "WEBSITE",
        "primary_platform_id": "https://ironmindperformance.com",
        "primary_platform_url": "https://ironmindperformance.com",
        "bio": "Online strength & conditioning coaching. Former Olympic weightlifting competitor. PhD in Exercise Science. Evidence-based training for serious lifters.",
        "website_url": "https://ironmindperformance.com",
        "social_links": {
            "instagram": "@ironmindcoach",
            "youtube": "@IronMindPerformance",
            "twitter": "@alexchencoach",
        },
        "niche_tags": ["strength", "coaching", "fitness", "powerlifting"],
        "location": "Portland, OR",
        "follower_count": 42000,
        "subscriber_count": 8500,
        "content_count": 245,
        "brand_colors": ["#2B2D42", "#8D99AE", "#EDF2F4"],
        "status": "SCRAPED",
        "content": [
            {
                "type": "blog",
                "title": "Why Your Squat Isn't Improving (And How to Fix It)",
                "body": "After coaching 500+ athletes, I've identified the 3 most common squat plateaus...",
            },
            {
                "type": "blog",
                "title": "Periodization for Natural Lifters: A Complete Guide",
                "body": "If you're not on gear, you need a different approach to programming...",
            },
            {
                "type": "blog",
                "title": "The Truth About Pre-Workout Supplements",
                "body": "I spent 6 months reviewing the research on every major pre-workout ingredient...",
            },
        ],
        "pricing": [
            {
                "tier": "Self-Guided Program",
                "price": 29.99,
                "interval": "month",
                "members": 0,
                "benefits": ["12-week program", "Exercise videos", "Progress tracker"],
            },
            {
                "tier": "Coached Athlete",
                "price": 199.00,
                "interval": "month",
                "members": 0,
                "benefits": [
                    "Custom programming",
                    "Weekly video review",
                    "Nutrition guidance",
                    "Competition prep",
                ],
            },
        ],
    },
    {
        "name": "Nourish & Thrive Wellness",
        "email": "sarah@nourishandthrive.co",
        "first_name": "Sarah",
        "last_name": "Williams",
        "primary_platform": "WEBSITE",
        "primary_platform_id": "https://nourishandthrive.co",
        "primary_platform_url": "https://nourishandthrive.co",
        "bio": "Holistic nutrition coach & certified health practitioner. Helping women heal their relationship with food through intuitive eating and functional nutrition. Featured in Women's Health & MindBodyGreen.",
        "website_url": "https://nourishandthrive.co",
        "social_links": {"instagram": "@nourishthrivesarah", "pinterest": "@nourishandthrive"},
        "niche_tags": ["nutrition", "wellness", "coaching", "weight_loss"],
        "location": "Nashville, TN",
        "follower_count": 31000,
        "subscriber_count": 12000,
        "content_count": 180,
        "brand_colors": ["#606C38", "#FEFAE0", "#DDA15E"],
        "status": "EMAIL_SENT",
        "content": [
            {
                "type": "blog",
                "title": "Stop Counting Calories: A Better Approach",
                "body": "After 10 years of disordered eating, I found a way to nourish my body without obsessing...",
            },
            {
                "type": "blog",
                "title": "Anti-Inflammatory Meal Prep (7 Days)",
                "body": "These are the exact meals I prep every Sunday for gut health and energy...",
            },
        ],
        "pricing": [
            {
                "tier": "Free Guide",
                "price": 0,
                "interval": "one_time",
                "members": 0,
                "benefits": ["7-day meal plan", "Shopping list", "Recipe ebook"],
            },
            {
                "tier": "1:1 Nutrition Coaching",
                "price": 149.00,
                "interval": "month",
                "members": 0,
                "benefits": [
                    "Bi-weekly calls",
                    "Custom meal plans",
                    "Lab review",
                    "Supplement protocol",
                ],
            },
            {
                "tier": "Group Program",
                "price": 59.00,
                "interval": "month",
                "members": 0,
                "benefits": ["Weekly group coaching", "Meal plans", "Community access"],
            },
        ],
    },
    {
        "name": "Movement Lab",
        "email": "info@movementlab.fit",
        "first_name": "Dan",
        "last_name": "Kowalski",
        "primary_platform": "WEBSITE",
        "primary_platform_id": "https://movementlab.fit",
        "primary_platform_url": "https://movementlab.fit",
        "bio": "Calisthenics & mobility coaching. I teach bodyweight strength, handstands, and movement flow. From zero pull-ups to muscle-ups in 12 weeks.",
        "website_url": "https://movementlab.fit",
        "social_links": {
            "instagram": "@movementlabdan",
            "youtube": "@MovementLabFit",
            "tiktok": "@movementlab",
        },
        "niche_tags": ["calisthenics", "fitness", "coaching", "wellness"],
        "location": "Berlin, Germany",
        "follower_count": 18500,
        "subscriber_count": 5200,
        "content_count": 120,
        "brand_colors": ["#0B132B", "#1C2541", "#5BC0BE"],
        "status": "DISCOVERED",
        "content": [
            {
                "type": "blog",
                "title": "Your First Muscle-Up: A Step-by-Step Guide",
                "body": "The muscle-up is the ultimate bodyweight strength test. Here's how to get there...",
            },
        ],
        "pricing": [
            {
                "tier": "Beginner Program",
                "price": 19.99,
                "interval": "month",
                "members": 0,
                "benefits": ["8-week program", "Video tutorials", "Progress tracking"],
            },
            {
                "tier": "Pro Coaching",
                "price": 129.00,
                "interval": "month",
                "members": 0,
                "benefits": [
                    "Custom programming",
                    "Video form checks",
                    "Monthly calls",
                    "Mobility assessments",
                ],
            },
        ],
    },
    # === PATREON (3) ===
    {
        "name": "Coach Kira Fitness",
        "email": "kira@coachkira.com",
        "first_name": "Kira",
        "last_name": "Johnson",
        "primary_platform": "PATREON",
        "primary_platform_id": "coachkira",
        "primary_platform_url": "https://www.patreon.com/coachkira",
        "bio": "IFBB Bikini Pro & online coach. Sharing workout programs, posing tutorials, and competition prep content. Helping women build confidence through bodybuilding.",
        "website_url": "https://coachkira.com",
        "social_links": {
            "instagram": "@coachkira_fit",
            "youtube": "@CoachKiraFitness",
            "tiktok": "@coachkira",
        },
        "niche_tags": ["fitness", "coaching", "nutrition", "strength"],
        "location": "Miami, FL",
        "follower_count": 65000,
        "subscriber_count": 1800,
        "content_count": 340,
        "brand_colors": ["#C9184A", "#FFD6FF", "#E7C6FF"],
        "status": "SCRAPED",
        "content": [
            {
                "type": "post",
                "title": "Glute Training: My Full Competition Prep Workout",
                "body": "This is the exact glute workout I used for my last show prep...",
            },
            {
                "type": "post",
                "title": "Macro Breakdown for Lean Bulking (Women)",
                "body": "Here's how I set up macros for my female clients who want to build muscle...",
            },
        ],
        "pricing": [
            {
                "tier": "Supporter",
                "price": 5.00,
                "interval": "month",
                "members": 890,
                "benefits": ["Early video access", "Behind the scenes"],
            },
            {
                "tier": "Workout Plans",
                "price": 15.00,
                "interval": "month",
                "members": 620,
                "benefits": ["Monthly workout plan", "Exercise demos", "Nutrition tips"],
            },
            {
                "tier": "VIP Coaching",
                "price": 50.00,
                "interval": "month",
                "members": 290,
                "benefits": [
                    "Custom training",
                    "Posing feedback",
                    "Competition prep",
                    "Private Discord",
                ],
            },
        ],
    },
    {
        "name": "MindStrong Meditation",
        "email": "raj@mindstrong.app",
        "first_name": "Raj",
        "last_name": "Mehta",
        "primary_platform": "PATREON",
        "primary_platform_id": "mindstrongmeditation",
        "primary_platform_url": "https://www.patreon.com/mindstrongmeditation",
        "bio": "Meditation teacher & mindfulness coach. 15 years of practice. I create guided meditations, breathwork sessions, and mindfulness courses for high-performers.",
        "social_links": {"instagram": "@mindstrongraj", "youtube": "@MindStrongMeditation"},
        "niche_tags": ["wellness", "meditation", "coaching", "yoga"],
        "location": "San Francisco, CA",
        "follower_count": 22000,
        "subscriber_count": 3400,
        "content_count": 210,
        "brand_colors": ["#264653", "#2A9D8F", "#E9C46A"],
        "status": "CONTENT_GENERATED",
        "content": [
            {
                "type": "post",
                "title": "10-Minute Morning Meditation for Focus",
                "body": "Start your day with this simple meditation that rewires your brain for deep work...",
            },
            {
                "type": "post",
                "title": "Breathwork for Sleep: Navy SEAL Box Breathing",
                "body": "This is the exact breathing technique used by Special Forces operators to fall asleep in 2 minutes...",
            },
        ],
        "pricing": [
            {
                "tier": "Meditator",
                "price": 7.00,
                "interval": "month",
                "members": 2100,
                "benefits": ["Weekly guided meditation", "Monthly breathwork session"],
            },
            {
                "tier": "Inner Circle",
                "price": 25.00,
                "interval": "month",
                "members": 890,
                "benefits": ["Daily meditations", "Live sessions", "Course library", "Community"],
            },
            {
                "tier": "1:1 Mentorship",
                "price": 100.00,
                "interval": "month",
                "members": 45,
                "benefits": ["Monthly coaching call", "Custom practice plan", "Priority support"],
            },
        ],
    },
    {
        "name": "RunWild Endurance",
        "email": "miles@runwild.co",
        "first_name": "Miles",
        "last_name": "Harper",
        "primary_platform": "PATREON",
        "primary_platform_id": "runwildendurance",
        "primary_platform_url": "https://www.patreon.com/runwildendurance",
        "bio": "Ultra marathon runner & endurance coach. 50+ ultras completed including Western States and UTMB. Sharing training plans, race reports, and gear reviews.",
        "social_links": {
            "instagram": "@runwildmiles",
            "strava": "miles_harper",
            "youtube": "@RunWildEndurance",
        },
        "niche_tags": ["cardio", "fitness", "coaching", "wellness"],
        "location": "Boulder, CO",
        "follower_count": 38000,
        "subscriber_count": 2800,
        "content_count": 175,
        "brand_colors": ["#3D5A80", "#98C1D9", "#E0FBFC"],
        "status": "SCRAPED",
        "content": [
            {
                "type": "post",
                "title": "How I Trained for Western States 100",
                "body": "Breaking down my 6-month training block for the world's oldest 100-mile race...",
            },
        ],
        "pricing": [
            {
                "tier": "Trail Crew",
                "price": 5.00,
                "interval": "month",
                "members": 1500,
                "benefits": ["Race reports", "Gear reviews", "Training tips"],
            },
            {
                "tier": "Training Plans",
                "price": 20.00,
                "interval": "month",
                "members": 850,
                "benefits": ["Monthly plan", "Pace calculator", "Race strategy"],
            },
            {
                "tier": "Coached Runner",
                "price": 75.00,
                "interval": "month",
                "members": 180,
                "benefits": ["Custom plan", "Weekly feedback", "Race day support"],
            },
        ],
    },
    # === ONLYFANS (3) ===
    {
        "name": "FitWithTanya",
        "email": "tanya@fitwith.me",
        "first_name": "Tanya",
        "last_name": "Brooks",
        "primary_platform": "ONLYFANS",
        "primary_platform_id": "fitwithtanya",
        "primary_platform_url": "https://onlyfans.com/fitwithtanya",
        "bio": "Certified personal trainer & bikini competitor. Daily workout videos, full-length training sessions, and nutrition coaching. SFW fitness content only. NASM-CPT.",
        "website_url": "https://fitwithtanya.com",
        "social_links": {
            "instagram": "@fitwithtanya_",
            "tiktok": "@fitwithtanya",
            "twitter": "@fitwithtanya",
        },
        "niche_tags": ["fitness", "strength", "nutrition", "coaching"],
        "location": "Los Angeles, CA",
        "follower_count": 120000,
        "subscriber_count": 8500,
        "content_count": 890,
        "brand_colors": ["#FF006E", "#FB5607", "#FFBE0B"],
        "status": "SCRAPED",
        "content": [
            {
                "type": "video",
                "title": "Full Body HIIT Workout (45 min)",
                "body": "Complete follow-along workout with warm-up and cool-down...",
            },
            {
                "type": "video",
                "title": "My Exact Meal Prep for Competition Season",
                "body": "Showing you every meal I eat during prep week...",
            },
        ],
        "pricing": [
            {
                "tier": "Monthly Sub",
                "price": 14.99,
                "interval": "month",
                "members": 8500,
                "benefits": ["Daily workouts", "Full-length videos", "DM access"],
            },
        ],
    },
    {
        "name": "StretchWithSoph",
        "email": "sophia@stretchflow.co",
        "first_name": "Sophia",
        "last_name": "Martinez",
        "primary_platform": "ONLYFANS",
        "primary_platform_id": "stretchwithsoph",
        "primary_platform_url": "https://onlyfans.com/stretchwithsoph",
        "bio": "Flexibility & mobility coach. Former ballet dancer. I help desk workers fix their posture, reduce pain, and get flexible in 15 min/day. RYT-200 yoga certified.",
        "social_links": {"instagram": "@stretchwithsoph", "youtube": "@StretchWithSoph"},
        "niche_tags": ["yoga", "wellness", "fitness", "pilates"],
        "location": "New York, NY",
        "follower_count": 85000,
        "subscriber_count": 5200,
        "content_count": 420,
        "brand_colors": ["#CDB4DB", "#FFC8DD", "#BDE0FE"],
        "status": "CONTENT_GENERATED",
        "content": [
            {
                "type": "video",
                "title": "15-Min Desk Worker Stretch Routine",
                "body": "If you sit all day, do this routine every evening to undo the damage...",
            },
            {
                "type": "video",
                "title": "Full Splits in 30 Days: Week 1",
                "body": "Progressive flexibility program starting from scratch...",
            },
        ],
        "pricing": [
            {
                "tier": "Monthly",
                "price": 9.99,
                "interval": "month",
                "members": 5200,
                "benefits": ["Daily stretch routines", "Mobility programs", "Q&A"],
            },
        ],
    },
    {
        "name": "CoachMikeStrength",
        "email": "mike@coachmike.fit",
        "first_name": "Mike",
        "last_name": "Davis",
        "primary_platform": "ONLYFANS",
        "primary_platform_id": "coachmikestrength",
        "primary_platform_url": "https://onlyfans.com/coachmikestrength",
        "bio": "Strength coach for beginners. I show you proper form on every exercise so you don't get hurt. No ego lifting, just results. 8 years coaching experience.",
        "social_links": {"instagram": "@coachmike_strength", "tiktok": "@coachmikefit"},
        "niche_tags": ["strength", "fitness", "coaching"],
        "location": "Chicago, IL",
        "follower_count": 45000,
        "subscriber_count": 3100,
        "content_count": 560,
        "brand_colors": ["#003049", "#D62828", "#F77F00"],
        "status": "DISCOVERED",
        "content": [
            {
                "type": "video",
                "title": "Deadlift Form Guide (Stop Rounding Your Back)",
                "body": "The deadlift is the king of exercises but only if you do it right...",
            },
        ],
        "pricing": [
            {
                "tier": "Monthly Sub",
                "price": 12.99,
                "interval": "month",
                "members": 3100,
                "benefits": ["Form tutorials", "Full workouts", "Program access"],
            },
        ],
    },
    # === KAJABI (3) ===
    {
        "name": "The Wellness Academy",
        "email": "dr.emma@wellnessacademy.io",
        "first_name": "Emma",
        "last_name": "Rodriguez",
        "primary_platform": "KAJABI",
        "primary_platform_id": "wellness-academy",
        "primary_platform_url": "https://wellnessacademy.mykajabi.com",
        "bio": "Doctor of Naturopathic Medicine. I teach evidence-based wellness through online courses. Specializing in gut health, hormones, and stress management. 20,000+ students enrolled.",
        "website_url": "https://wellnessacademy.io",
        "social_links": {
            "instagram": "@dremmawellness",
            "youtube": "@WellnessAcademy",
            "linkedin": "emmarod-nd",
        },
        "niche_tags": ["wellness", "nutrition", "coaching"],
        "location": "Vancouver, BC",
        "follower_count": 55000,
        "subscriber_count": 20000,
        "content_count": 340,
        "brand_colors": ["#588157", "#A3B18A", "#DAD7CD"],
        "status": "SCRAPED",
        "content": [
            {
                "type": "course",
                "title": "Gut Health Masterclass",
                "body": "A 6-week deep dive into healing your gut microbiome through food, supplements, and lifestyle changes...",
            },
            {
                "type": "course",
                "title": "Hormone Reset for Women 40+",
                "body": "Evidence-based strategies for managing perimenopause and menopause naturally...",
            },
            {
                "type": "blog",
                "title": "Top 10 Anti-Inflammatory Foods You Should Eat Daily",
                "body": "Chronic inflammation is the root of most modern disease. Here are the foods that fight it...",
            },
        ],
        "pricing": [
            {
                "tier": "Single Course",
                "price": 197.00,
                "interval": "one_time",
                "members": 8500,
                "benefits": ["Lifetime access", "Course materials", "Community forum"],
            },
            {
                "tier": "All-Access Pass",
                "price": 49.00,
                "interval": "month",
                "members": 4200,
                "benefits": ["All courses", "Monthly live Q&A", "Resource library", "Community"],
            },
            {
                "tier": "Practitioner Program",
                "price": 997.00,
                "interval": "one_time",
                "members": 650,
                "benefits": [
                    "Certification",
                    "Client protocols",
                    "Business training",
                    "Mentorship",
                ],
            },
        ],
    },
    {
        "name": "Peak Performance Lab",
        "email": "jordan@peakperformancelab.com",
        "first_name": "Jordan",
        "last_name": "Blake",
        "primary_platform": "KAJABI",
        "primary_platform_id": "peak-performance-lab",
        "primary_platform_url": "https://peakperformancelab.mykajabi.com",
        "bio": "Sports psychologist & mental performance coach. I help athletes and entrepreneurs unlock peak performance through mindset training, visualization, and habit science.",
        "website_url": "https://peakperformancelab.com",
        "social_links": {
            "instagram": "@peakperformancelab",
            "youtube": "@PeakPerfLab",
            "twitter": "@jordanblake_pp",
        },
        "niche_tags": ["coaching", "wellness", "fitness"],
        "location": "Scottsdale, AZ",
        "follower_count": 33000,
        "subscriber_count": 7800,
        "content_count": 195,
        "brand_colors": ["#14213D", "#FCA311", "#E5E5E5"],
        "status": "STORE_CREATED",
        "content": [
            {
                "type": "course",
                "title": "The Champion's Mindset",
                "body": "A 4-week program to develop the mental toughness of elite athletes...",
            },
            {
                "type": "course",
                "title": "Visualization Mastery for Athletes",
                "body": "Learn the exact visualization techniques used by Olympic gold medalists...",
            },
        ],
        "pricing": [
            {
                "tier": "Mindset Course",
                "price": 147.00,
                "interval": "one_time",
                "members": 3200,
                "benefits": ["4-week program", "Workbook", "Audio sessions"],
            },
            {
                "tier": "Monthly Membership",
                "price": 39.00,
                "interval": "month",
                "members": 2100,
                "benefits": [
                    "All courses",
                    "Weekly live sessions",
                    "Community",
                    "New content monthly",
                ],
            },
            {
                "tier": "Elite 1:1 Coaching",
                "price": 500.00,
                "interval": "month",
                "members": 25,
                "benefits": [
                    "Weekly sessions",
                    "Custom protocols",
                    "24/7 support",
                    "Performance tracking",
                ],
            },
        ],
    },
    {
        "name": "Pilates with Priya",
        "email": "priya@pilateswithpriya.com",
        "first_name": "Priya",
        "last_name": "Sharma",
        "primary_platform": "KAJABI",
        "primary_platform_id": "pilates-with-priya",
        "primary_platform_url": "https://pilateswithpriya.mykajabi.com",
        "bio": "Comprehensive Pilates instructor & teacher trainer. BASI-certified. Teaching mat & reformer Pilates online since 2019. 15,000+ students in 40 countries.",
        "website_url": "https://pilateswithpriya.com",
        "social_links": {"instagram": "@pilateswithpriya", "youtube": "@PilatesWithPriya"},
        "niche_tags": ["pilates", "fitness", "wellness", "coaching"],
        "location": "London, UK",
        "follower_count": 48000,
        "subscriber_count": 15000,
        "content_count": 280,
        "brand_colors": ["#B5838D", "#E5989B", "#FFB4A2"],
        "status": "EMAIL_SENT",
        "content": [
            {
                "type": "course",
                "title": "Beginner Mat Pilates (8 Weeks)",
                "body": "Build your foundation with this structured beginner program covering all fundamental movements...",
            },
            {
                "type": "course",
                "title": "Pilates for Runners",
                "body": "Cross-training program specifically designed to prevent running injuries and improve performance...",
            },
            {
                "type": "blog",
                "title": "Pilates vs Yoga: Which Is Right for You?",
                "body": "I'm certified in both, and here's my honest comparison for different goals...",
            },
        ],
        "pricing": [
            {
                "tier": "Single Course",
                "price": 79.00,
                "interval": "one_time",
                "members": 6500,
                "benefits": ["Lifetime access", "Downloadable workouts"],
            },
            {
                "tier": "Studio Membership",
                "price": 29.00,
                "interval": "month",
                "members": 4800,
                "benefits": [
                    "All courses",
                    "Live classes 3x/week",
                    "Community",
                    "New programs monthly",
                ],
            },
            {
                "tier": "Teacher Training",
                "price": 1497.00,
                "interval": "one_time",
                "members": 320,
                "benefits": [
                    "Full certification",
                    "Anatomy modules",
                    "Teaching practice",
                    "Business mentorship",
                ],
            },
        ],
    },
]


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    inserted = 0

    for coach in COACHES:
        # Check if email already exists
        cur.execute("SELECT id FROM prospects WHERE email = %s", (coach["email"],))
        if cur.fetchone():
            print(f"  Skipping {coach['name']} (email exists)")
            continue

        # Insert prospect
        cur.execute(
            """
            INSERT INTO prospects (
                name, email, first_name, last_name,
                primary_platform, primary_platform_id, primary_platform_url,
                bio, website_url, social_links, niche_tags, location,
                follower_count, subscriber_count, content_count,
                brand_colors, status
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s
            ) RETURNING id
        """,
            (
                coach["name"],
                coach["email"],
                coach["first_name"],
                coach["last_name"],
                coach["primary_platform"],
                coach["primary_platform_id"],
                coach["primary_platform_url"],
                coach["bio"],
                coach.get("website_url"),
                json.dumps(coach.get("social_links", {})),
                json.dumps(coach.get("niche_tags", [])),
                coach.get("location"),
                coach["follower_count"],
                coach["subscriber_count"],
                coach["content_count"],
                json.dumps(coach.get("brand_colors", [])),
                coach["status"],
            ),
        )
        prospect_id = cur.fetchone()[0]

        # Insert platform profile
        cur.execute(
            """
            INSERT INTO platform_profiles (prospect_id, platform, platform_id, platform_url)
            VALUES (%s, %s, %s, %s)
        """,
            (
                prospect_id,
                coach["primary_platform"],
                coach["primary_platform_id"],
                coach["primary_platform_url"],
            ),
        )

        # Insert scraped content
        for i, content in enumerate(coach.get("content", [])):
            cur.execute(
                """
                INSERT INTO scraped_content (
                    prospect_id, platform, content_type, title, body,
                    view_count, engagement_count, tags
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    prospect_id,
                    coach["primary_platform"],
                    content["type"],
                    content["title"],
                    content["body"],
                    (i + 1) * 5000,
                    (i + 1) * 200,
                    json.dumps(coach.get("niche_tags", [])),
                ),
            )

        # Insert pricing tiers
        for tier in coach.get("pricing", []):
            cur.execute(
                """
                INSERT INTO scraped_pricing (
                    prospect_id, platform, tier_name, price_amount,
                    currency, interval, benefits, member_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    prospect_id,
                    coach["primary_platform"],
                    tier["tier"],
                    tier["price"],
                    "USD",
                    tier["interval"],
                    json.dumps(tier["benefits"]),
                    tier["members"],
                ),
            )

        inserted += 1
        print(f"  [{coach['primary_platform']:>10}] {coach['name']} — {coach['status']}")

    conn.commit()
    conn.close()

    print(f"\nSeeded {inserted} test coaches across 5 platforms.")

    # Summary
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(
        "SELECT primary_platform, COUNT(*) FROM prospects GROUP BY primary_platform ORDER BY COUNT(*) DESC"
    )
    print("\nPlatform breakdown:")
    for row in cur.fetchall():
        print(f"  {row[0]:<12} {row[1]}")
    cur.execute("SELECT COUNT(*) FROM prospects")
    print(f"\nTotal prospects: {cur.fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    main()
