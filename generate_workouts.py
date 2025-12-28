import pandas as pd
import random
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors

TESTING_DATA_FILE = 'athlete_testing.csv'
OUTPUT_DIR = 'output'
LOGO_FILE = 'phs_football_logo.png'

MESOCYCLES = [
    {
        'name': 'Phase 1',
        'start_date': datetime(2026, 1, 5),
        'weeks': 4,
        'main_intensity_min': 0.60,
        'main_intensity_max': 0.75,
        'main_reps': '8-10',
        'main_sets': '3',
    },
    {
        'name': 'Phase 2',
        'start_date': datetime(2026, 2, 2),
        'weeks': 4,
        'main_intensity_min': 0.70,
        'main_intensity_max': 0.80,
        'main_reps': '6-8',
        'main_sets': '3',
    },
    {
        'name': 'Phase 3',
        'start_date': datetime(2026, 3, 2),
        'weeks': 4,
        'main_intensity_min': 0.80,
        'main_intensity_max': 0.90,
        'main_reps': '3-5',
        'main_sets': '4',
    },
]

COLOR_BLACK = colors.HexColor('#000000')
COLOR_GOLD = colors.HexColor('#C9AE5D')
COLOR_DARK_GOLD = colors.HexColor('#8B7520')
COLOR_LIGHT_GOLD = colors.HexColor('#F9F6F0')

EXERCISE_POOLS = {
    'Monday': {
        'core': [
            {
                'name': 'Back Squat',
                'reps': None,
                'ref_max': 'Squat',
                'factor': 'MAIN',
                'is_core': True,
                'notes': 'Main lift—focus on depth, tight core, and controlled descent.',
            },
        ],
        'accessories': [
            {'name': 'Front Squat', 'reps': '6-8', 'ref_max': 'Squat', 'factor': 0.65,
             'is_core': False, 'notes': 'Lighter variation; keep elbows high.'},
            {'name': 'Goblet Squat', 'reps': '10-12', 'ref_max': 'Squat', 'factor': 0.25,
             'is_core': False, 'notes': 'Single DB; stay upright and control each rep.'},
            {'name': 'Split Squat', 'reps': '8-10/leg', 'ref_max': 'Squat', 'factor': 0.30,
             'is_core': False, 'notes': 'Total DB load; long stride, controlled depth.'},
            {'name': 'Walking Lunges', 'reps': '8-10/leg', 'ref_max': 'Squat', 'factor': 0.25,
             'is_core': False, 'notes': 'DB or bodyweight; big steps, knee behind toes.'},
            {'name': 'Lateral Lunges', 'reps': '8-10/side', 'ref_max': 'Squat', 'factor': 0.20,
             'is_core': False, 'notes': 'Light DB; sit back into hip, keep knee over foot.'},
            {'name': 'Step-ups', 'reps': '8-10/leg', 'ref_max': 'Squat', 'factor': 0.25,
             'is_core': False, 'notes': 'DB; drive through whole foot on box.'},
            {'name': 'Leg Press', 'reps': '10-12', 'ref_max': 'Squat', 'factor': 0.70,
             'is_core': False, 'notes': 'Control depth; no bouncing off the stops.'},
            {'name': 'Glute Bridge', 'reps': '8-12', 'ref_max': 'Deadlift', 'factor': 0.60,
             'is_core': False, 'notes': 'Drive hips up and pause at the top.'},
            {'name': 'Glute-Ham Raise', 'reps': '6-10', 'ref_max': 'Deadlift', 'factor': 0.05,
             'is_core': False, 'notes': 'Mostly bodyweight; use assistance if needed.'},
            {'name': 'Hamstring Curl', 'reps': '10-15', 'ref_max': 'Deadlift', 'factor': 0.20,
             'is_core': False, 'notes': 'Smooth reps; squeeze at the top.'},
            {'name': 'Calf Raises', 'reps': '12-20', 'ref_max': 'Squat', 'factor': 0.25,
             'is_core': False, 'notes': 'Full range of motion and pause at the top.'},
            {'name': 'Plank', 'reps': '30-45 sec', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Keep body straight; no sagging hips.'},
            {'name': 'Pallof Press', 'reps': '10-15/side', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Light band/cable; resist rotation.'},
        ],
    },
    'Tuesday': {
        'core': [
            {
                'name': 'Bench Press',
                'reps': None,
                'ref_max': 'Bench Press',
                'factor': 'MAIN',
                'is_core': True,
                'notes': 'Main lift—touch the chest and press under control.',
            },
        ],
        'accessories': [
            {'name': 'Close-Grip Bench', 'reps': '6-8', 'ref_max': 'Bench Press', 'factor': 0.65,
             'is_core': False, 'notes': 'Hands just inside shoulders; tricep emphasis.'},
            {'name': 'DB Flat Bench', 'reps': '8-10', 'ref_max': 'Bench Press', 'factor': 0.65,
             'is_core': False, 'notes': 'Total DB load ≈ 60–70% of your bench max.'},
            {'name': 'DB Incline Bench', 'reps': '8-10', 'ref_max': 'Bench Press', 'factor': 0.60,
             'is_core': False, 'notes': 'Press up and slightly back; control the descent.'},
            {'name': 'Push-ups', 'reps': '8-15', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Full range; add weight only when sets are easy.'},
            {'name': 'Dips', 'reps': '6-10', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Assisted if needed; stay upright for triceps.'},
            {'name': 'Barbell Row', 'reps': '8-10', 'ref_max': 'Bench Press', 'factor': 0.65,
             'is_core': False, 'notes': 'Flat back; pull bar to mid-torso.'},
            {'name': 'DB Row', 'reps': '8-12/arm', 'ref_max': 'Bench Press', 'factor': 0.30,
             'is_core': False, 'notes': 'Use a bench for support; no torso twisting.'},
            {'name': 'Skullcrushers', 'reps': '10-12', 'ref_max': 'Bench Press', 'factor': 0.25,
             'is_core': False, 'notes': 'Lower to forehead; elbows stay in.'},
            {'name': 'Cable Pushdowns', 'reps': '10-15', 'ref_max': 'Bench Press', 'factor': 0.20,
             'is_core': False, 'notes': 'Keep upper arms pinned; small controlled movement.'},
            {'name': 'Face Pulls', 'reps': '12-15', 'ref_max': 'Bench Press', 'factor': 0.15,
             'is_core': False, 'notes': 'Pull to forehead with elbows high.'},
            {'name': 'Band Pull-Aparts', 'reps': '15-20', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Keep arms straight; squeeze shoulder blades together.'},
            {'name': 'Bicep Curls', 'reps': '10-12', 'ref_max': 'Bench Press', 'factor': 0.18,
             'is_core': False, 'notes': 'No swinging; keep elbows near your sides.'},
        ],
    },
    'Wednesday': {
        'core': [
            {
                'name': 'Deadlift',
                'reps': None,
                'ref_max': 'Deadlift',
                'factor': 'MAIN',
                'is_core': True,
                'notes': 'Main lift. Bar close, flat back, feet anchored in floor.',
            },
        ],
        'accessories': [
            {'name': 'Trap-Bar Deadlift', 'reps': '6-8', 'ref_max': 'Deadlift', 'factor': 0.65,
             'is_core': False, 'notes': 'Handles at your sides; strong lockout at the top.'},
            {'name': 'Romanian Deadlift', 'reps': '8-10', 'ref_max': 'Deadlift', 'factor': 0.60,
             'is_core': False, 'notes': 'Soft knees; push hips back until hamstrings stretch.'},
            {'name': 'Single-Leg RDL', 'reps': '8-10/leg', 'ref_max': 'Deadlift', 'factor': 0.25,
             'is_core': False, 'notes': 'Use DBs; keep hips square, control balance.'},
            {'name': 'Good Mornings', 'reps': '8-10', 'ref_max': 'Squat', 'factor': 0.35,
             'is_core': False, 'notes': 'Light bar; hinge at hips, not spine.'},
            {'name': 'KB Swings', 'reps': '12-15', 'ref_max': 'Deadlift', 'factor': 0.25,
             'is_core': False, 'notes': 'Explosive hip snap; bell should float at chest height.'},
            {'name': 'Bulgarian Split Squat', 'reps': '8-10/leg', 'ref_max': 'Squat', 'factor': 0.30,
             'is_core': False, 'notes': 'Rear foot elevated; forward knee over toes.'},
            {'name': 'Leg Curl', 'reps': '8-12', 'ref_max': 'Deadlift', 'factor': 0.20,
             'is_core': False, 'notes': 'Hamstrings only; smooth range, no bouncing.'},
            {'name': 'Reverse Hyperextensions', 'reps': '10-15', 'ref_max': 'Deadlift', 'factor': 0.25,
             'is_core': False, 'notes': 'Light load; squeeze glutes at top.'},
            {'name': 'Hanging Leg Raises', 'reps': '8-12', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Control the swing; raise legs with abs.'},
        ],
    },
    'Thursday': {
        'core': [
            {
                'name': 'Standing Military Press',
                'reps': None,
                'ref_max': 'Shoulder Press',
                'factor': 'MAIN',
                'is_core': True,
                'notes': 'Strict press; no leg drive, lock out overhead.',
            },
        ],
        'accessories': [
            {'name': 'Push Press', 'reps': '5-6', 'ref_max': 'Shoulder Press', 'factor': 0.75,
             'is_core': False, 'notes': 'Use a small leg dip to drive the bar overhead.'},
            {'name': 'DB Shoulder Press', 'reps': '8-10', 'ref_max': 'Shoulder Press', 'factor': 0.75,
             'is_core': False, 'notes': 'Total DB load ~70–80% of your press max.'},
            {'name': 'Single-Arm Landmine Press', 'reps': '8-10/side', 'ref_max': 'Shoulder Press', 'factor': 0.50,
             'is_core': False, 'notes': 'Press bar away at 45° angle; control the eccentric.'},
            {'name': 'Pull-ups', 'reps': '6-10', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Strict reps; chin over bar, full hang each rep.'},
            {'name': 'Chin-ups', 'reps': '6-10', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Underhand grip; focus on full range of motion.'},
            {'name': 'Lat Pulldown', 'reps': '8-12', 'ref_max': 'Bench Press', 'factor': 0.55,
             'is_core': False, 'notes': 'Pull bar to chest; slight lean back, no swinging.'},
            {'name': 'TRX Rows', 'reps': '8-12', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Bodyweight row; walk feet forward to make it harder.'},
            {'name': 'Lateral Raises', 'reps': '12-15', 'ref_max': 'Shoulder Press', 'factor': 0.08,
             'is_core': False, 'notes': 'Light DBs; raise to shoulder height with control.'},
            {'name': 'Rear Delt Flyes', 'reps': '12-15', 'ref_max': 'Shoulder Press', 'factor': 0.08,
             'is_core': False, 'notes': 'Hinge forward; squeeze shoulder blades together.'},
            {'name': 'Upright Rows', 'reps': '10-12', 'ref_max': 'Shoulder Press', 'factor': 0.25,
             'is_core': False, 'notes': 'Light bar or DBs; stop at upper-chest height.'},
            {'name': 'Band External Rotations', 'reps': '12-20', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Very light band; elbow at side, rotate forearm out.'},
            {'name': "Farmer's Carries", 'reps': '20-30 yds', 'ref_max': None, 'factor': None,
             'is_core': False, 'notes': 'Heavy DBs; stand tall and walk with control.'},
            {'name': 'Shrugs', 'reps': '12-15', 'ref_max': 'Deadlift', 'factor': 0.20,
             'is_core': False, 'notes': 'Lift shoulders straight up; hold briefly at top.'},
        ],
    },
}

BODYWEIGHT_EXERCISES = {
    'Push-ups', 'Dips', 'TRX Rows', 'Plank', 'Pallof Press',
    'Glute-Ham Raise', 'Hanging Leg Raises',
    'Band Pull-Aparts', 'Band External Rotations',
    'Pull-ups', 'Chin-ups', 'Reverse Hyperextensions'
}

def clean_test_value(val):
    if pd.isna(val) or val == 'N/A' or val == '':
        return None
    if isinstance(val, str):
        parts = val.split()
        try:
            return float(''.join(c for c in parts[0] if c.isdigit() or c == '.'))
        except Exception:
            return None
    return float(val)

def calculate_target_weight(max_weight, factor, round_to=5):
    if max_weight is None or factor is None:
        return None
    target = max_weight * factor
    return int(round(target / round_to) * round_to)

def pick_day_exercises(day, random_state, prev_accessory_names=None):
    cfg = EXERCISE_POOLS[day]
    core = cfg['core']
    accessories = cfg['accessories']
    rs = random.Random(random_state + hash(day))

    if prev_accessory_names:
        pool = [a for a in accessories if a['name'] not in prev_accessory_names]
        if len(pool) < 3:
            pool = accessories[:]
    else:
        pool = accessories[:]

    selected = rs.sample(pool, min(3, len(pool)))
    return core + selected, [a['name'] for a in selected]

def generate_week_template_for_meso(meso_cfg, global_week_number, prev_week_accessories_by_day):
    weeks = meso_cfg['weeks']
    i_min = meso_cfg['main_intensity_min']
    i_max = meso_cfg['main_intensity_max']
    local_week = ((global_week_number - 1) % weeks) + 1
    intensity = i_min + (i_max - i_min) * ((local_week - 1) / max(weeks - 1, 1))

    template = {}
    new_prev = {}

    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']:
        prev_accessories = prev_week_accessories_by_day.get(day)
        exs, used_accessories = pick_day_exercises(day, random_state=global_week_number,
                                                   prev_accessory_names=prev_accessories)

        rows = []
        for ex in exs:
            reps = ex['reps']
            if ex['is_core']:
                reps = meso_cfg['main_reps']
            rows.append({
                'name': ex['name'],
                'reps': reps,
                'ref_max': ex['ref_max'],
                'factor': ex['factor'],
                'is_core': ex['is_core'],
                'notes': ex['notes'],
            })
        template[day] = {'rows': rows, 'intensity': intensity}
        new_prev[day] = used_accessories

    return template, new_prev

def instantiate_week_for_athlete(athlete_maxes, meso_cfg, global_week_number, template):
    plan = {}
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']:
        day_info = template[day]
        rows = []
        for ex in day_info['rows']:
            name = ex['name']
            reps = ex['reps']
            ref_max = ex['ref_max']
            factor = ex['factor']
            notes = ex['notes']
            is_core = ex['is_core']

            if is_core:
                sets = meso_cfg['main_sets']
                if factor == 'MAIN':
                    if day == 'Monday':
                        max_val = athlete_maxes.get('Squat')
                    elif day == 'Tuesday':
                        max_val = athlete_maxes.get('Bench Press')
                    elif day == 'Wednesday':
                        max_val = athlete_maxes.get('Deadlift')
                    else:
                        max_val = athlete_maxes.get('Shoulder Press')
                    target = calculate_target_weight(max_val, day_info['intensity'])
                else:
                    max_val = athlete_maxes.get(ref_max) if ref_max else None
                    target = calculate_target_weight(max_val, factor)
            else:
                sets = '3' if meso_cfg['name'] in ['Phase 1', 'Phase 2'] else '4'
                if ref_max is None or factor is None:
                    target = None
                else:
                    max_val = athlete_maxes.get(ref_max)
                    target = calculate_target_weight(max_val, factor)

            rows.append({
                'exercise': name,
                'sets': sets,
                'reps': reps,
                'target_weight': target,
                'notes': notes,
            })
        plan[day] = rows
    return plan

def build_week_pdf(filename, athlete_name, meso_cfg, global_week_number, local_week_number, start_date, week_plan):
    doc = SimpleDocTemplate(
        filename,
        pagesize=portrait(letter),
        topMargin=0.35 * inch,
        bottomMargin=0.35 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    story = []

    title_style = ParagraphStyle('TitleStyle', fontSize=24, textColor=COLOR_BLACK, alignment=1, spaceAfter=12)
    story.append(Paragraph("<b>PHS FOOTBALL POWER PROGRAM</b>", title_style))
    story.append(Spacer(1, 0.20 * inch))

    if os.path.exists(LOGO_FILE):
        try:
            logo_obj = Image(LOGO_FILE)
            logo_obj._restrictSize(1.6 * inch, 1.6 * inch)
        except Exception as e:
            print(f"Warning: could not load logo: {e}")
            logo_obj = Paragraph(" ", getSampleStyleSheet()['Normal'])
    else:
        print(f"Warning: logo file '{LOGO_FILE}' not found")
        logo_obj = Paragraph(" ", getSampleStyleSheet()['Normal'])

    logo_table = Table([[logo_obj]], colWidths=[7.0 * inch])
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(logo_table)
    story.append(Spacer(1, 0.18 * inch))

    block_name = meso_cfg['name']
    info_text = f"<b>{athlete_name}</b> | <b>{block_name}</b> | <b>Week {local_week_number}</b> | {start_date.strftime('%b %d, %Y')}"
    info_style = ParagraphStyle('InfoStyle', fontSize=13, textColor=COLOR_BLACK, alignment=1, spaceAfter=10)
    story.append(Paragraph(info_text, info_style))

    col_widths = [2.0 * inch, 0.5 * inch, 1.0 * inch, 0.9 * inch, 0.9 * inch, 1.4 * inch]
    total_width = sum(col_widths)

    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']:
        if day not in week_plan:
            continue

        day_header_tbl = Table(
            [[Paragraph(day, ParagraphStyle('DayStyle', fontSize=11, textColor=COLOR_GOLD))]],
            colWidths=[total_width],
        )
        day_header_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_BLACK),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(day_header_tbl)

        data = [['Exercise', 'Sets', 'Targeted Reps', 'Target Wt.', 'Actual Reps', 'Notes']]
        for row in week_plan[day]:
            name = row['exercise']
            target = row['target_weight']
            if name in BODYWEIGHT_EXERCISES:
                weight_str = 'BW / Light'
            else:
                if target is None:
                    weight_str = '45 lb'
                else:
                    weight_str = f"{target} lb"

            data.append([
                Paragraph(name, ParagraphStyle('Cell', fontSize=8)),
                Paragraph(str(row['sets']), ParagraphStyle('Cell', fontSize=8, alignment=1)),
                Paragraph(row['reps'], ParagraphStyle('Cell', fontSize=8, alignment=1)),
                Paragraph(weight_str, ParagraphStyle('Cell', fontSize=8, alignment=1)),
                Paragraph('', ParagraphStyle('Cell', fontSize=8, alignment=1)),
                Paragraph(row['notes'], ParagraphStyle('NotesCell', fontSize=7.5, leading=8)),
            ])

        tbl = Table(data, colWidths=col_widths)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_GOLD),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLACK),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
            ('TOPPADDING', (0, 0), (-1, 0), 3),

            ('GRID', (0, 0), (-1, -1), 0.4, COLOR_BLACK),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 1), (-1, -1), 3),
            ('RIGHTPADDING', (0, 1), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),

            ('ALIGN', (1, 1), (4, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (5, 1), (5, -1), 'LEFT'),

            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_GOLD]),
        ]))

        story.append(tbl)
        story.append(Spacer(1, 0.04 * inch))

    doc.build(story)

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    df = pd.read_csv(TESTING_DATA_FILE)
    print(f"Loaded {len(df)} athletes from {TESTING_DATA_FILE}")

    weekly_templates = {}
    prev_accessories_by_day = {'Monday': None, 'Tuesday': None, 'Wednesday': None, 'Thursday': None}
    global_week_counter = 1
    for meso in MESOCYCLES:
        for _ in range(meso['weeks']):
            template, prev_accessories_by_day = generate_week_template_for_meso(
                meso, global_week_counter, prev_accessories_by_day
            )
            weekly_templates[global_week_counter] = (meso, template)
            global_week_counter += 1

    for _, row in df.iterrows():
        name = row['Name']
        print(f"\n=== Generating workouts for {name} ===")

        maxes = {
            'Bench Press': clean_test_value(row.get('Bench Press')),
            'Squat': clean_test_value(row.get('Squat')),
            'Deadlift': clean_test_value(row.get('Deadlift')),
            'Shoulder Press': clean_test_value(row.get('Shoulder Press')),
        }
        print(f"  Maxes: {maxes}")

        athlete_folder = os.path.join(OUTPUT_DIR, name.replace(' ', '_'))
        if not os.path.exists(athlete_folder):
            os.makedirs(athlete_folder)

        global_week = 1
        for meso in MESOCYCLES:
            start_date = meso['start_date']
            for local_week in range(1, meso['weeks'] + 1):
                _, template = weekly_templates[global_week]
                plan = instantiate_week_for_athlete(maxes, meso, global_week, template)

                filename = os.path.join(
                    athlete_folder,
                    f"{name.replace(' ', '_')}_Week{global_week:02d}_{meso['name'].replace(' ', '')}.pdf"
                )

                build_week_pdf(
                    filename=filename,
                    athlete_name=name,
                    meso_cfg=meso,
                    global_week_number=global_week,
                    local_week_number=local_week,
                    start_date=start_date,
                    week_plan=plan,
                )

                print(f"  Created: {filename}")

                start_date += timedelta(days=7)
                global_week += 1

    print(f"\nAll PDFs generated in '{OUTPUT_DIR}' folder.")

if __name__ == '__main__':
    main()
