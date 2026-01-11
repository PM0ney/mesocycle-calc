import pandas as pd
import random
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib import colors

# =========================
# COLORS
# =========================

COLOR_BLACK = colors.HexColor('#000000')
COLOR_GOLD = colors.HexColor('#C9AE5D')
COLOR_DARK_GOLD = colors.HexColor('#8B7520')
COLOR_LIGHT_GOLD = colors.HexColor('#F9F6F0')
ROW_BG_LIGHT = COLOR_LIGHT_GOLD
ROW_BG_MED = colors.white # alternate with white

# =========================
# CONFIGURATION
# =========================

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
        'main_reps': '8–10',
        'main_sets': '3',
    },
    {
        'name': 'Phase 2',
        'start_date': datetime(2026, 2, 2),
        'weeks': 4,
        'main_intensity_min': 0.70,
        'main_intensity_max': 0.80,
        'main_reps': '6–8',
        'main_sets': '3',
    },
    {
        'name': 'Phase 3',
        'start_date': datetime(2026, 3, 2),
        'weeks': 4,
        'main_intensity_min': 0.80,
        'main_intensity_max': 0.90,
        'main_reps': '3–5',
        'main_sets': '4',
    },
]

# =========================
# ACCESSORY INTENSITY BY PHASE
# =========================
# Multiplier applied to exercise 'factor' based on phase rep range
# This makes accessories progress with volume/intensity like main lifts

ACCESSORY_INTENSITY = {
    0: 0.65,  # Phase 1: 8-10 reps (higher volume = lower intensity)
    1: 0.75,  # Phase 2: 6-8 reps
    2: 0.90,  # Phase 3: 3-5 reps (lower volume = higher intensity)
}

MAIN_LIFTS = {
    'Monday': 'Back Squat',
    'Tuesday': 'Bench Press',
    'Wednesday': 'Deadlift',
    'Thursday': 'Standing Military Press',
}

MAIN_LIFT_MAXES = {
    'Back Squat': 'Back Squat',
    'Bench Press': 'Bench Press',
    'Deadlift': 'Deadlift',
    'Standing Military Press': 'Shoulder Press',
}

# Guaranteed accessories that always appear (not randomly selected)
# Tuesday Phase 1 & 2: Bench Press (main), TRX Rows, Cable Pushdowns, DB Incline Bench
GUARANTEED_ACCESSORIES = {
    'Thursday': [
        {'name': 'Push Press', 'ref_max': 'Shoulder Press','factor': 1.15, 'is_push_press': True},
    ]
}

# Phase-specific guaranteed accessories for Tuesday (Phase 1 & 2 only)
# TRX Rows counts as both guaranteed AND the bodyweight exercise
TUESDAY_PHASE_1_2_GUARANTEED = [
    {'name': 'TRX Rows (failure)', 'ref_max': None, 'factor': None},
    {'name': 'Cable Pushdowns', 'ref_max': 'Bench Press', 'factor': 0.25},
    {'name': 'DB Incline Bench', 'ref_max': 'Bench Press', 'factor': 0.60},
]

# Days with guaranteed accessories need fewer random accessories
RANDOM_ACCESSORY_COUNT = {
    'Monday': 3,
    'Tuesday': 3,  # Phase 1 & 2: only guaranteed exercises; Phase 3: 1 main + 3 random = 4 total
    'Wednesday': 3,
    'Thursday': 2,  # 1 main + 1 guaranteed + 2 random = 4 total
}

BODYWEIGHT_EXERCISES = {
    'Push-ups (failure)', 'Dips (failure)', 'TRX Rows (failure)',
    'Glute-Ham Raise (failure)', 'Hanging Leg Raises (failure)',
    'Dead Arm Hang (failure)', 'Reverse Hyperext (failure)'
}

# Day-specific bodyweight exercise pools
BODYWEIGHT_BY_DAY = {
    'Monday': ['Glute-Ham Raise (failure)', 'Hanging Leg Raises (failure)'],
    'Tuesday': ['Push-ups (failure)', 'TRX Rows (failure)'],
    'Wednesday': ['Reverse Hyperext (failure)', 'Hanging Leg Raises (failure)'],
    'Thursday': ['Dead Arm Hang (failure)'],
}

EXERCISE_POOLS = {
    'Monday': [
        {'name': 'Back Squat', 'ref_max': 'Back Squat', 'factor': None}, # main lift
        {'name': 'Front Squat', 'ref_max': 'Back Squat', 'factor': 0.85},
        {'name': 'Goblet Squat', 'ref_max': 'Back Squat', 'factor': 0.30},
        {'name': 'Split Squat', 'ref_max': 'Back Squat', 'factor': 0.35},
        {'name': 'Walking Lunges', 'ref_max': 'Back Squat', 'factor': 0.30},
        {'name': 'Lateral Lunges', 'ref_max': 'Back Squat', 'factor': 0.25},
        {'name': 'Step-ups', 'ref_max': 'Back Squat', 'factor': 0.30},
        {'name': 'Leg Press', 'ref_max': 'Back Squat', 'factor': 0.80},
        {'name': 'Glute Bridge', 'ref_max': 'Deadlift', 'factor': 0.70},
        {'name': 'Glute-Ham Raise (failure)', 'ref_max': 'Deadlift', 'factor': 0.10}, # BW exercise
        {'name': 'Hamstring Curl', 'ref_max': 'Deadlift', 'factor': 0.30},
        {'name': 'Calf Raises', 'ref_max': 'Back Squat', 'factor': 0.40},
    ],
    'Tuesday': [
        {'name': 'Bench Press', 'ref_max': 'Bench Press','factor': None}, # main lift
        {'name': 'Close-Grip Bench', 'ref_max': 'Bench Press','factor': 0.90},
        {'name': 'DB Flat Bench', 'ref_max': 'Bench Press','factor': 0.60},
        {'name': 'DB Incline Bench', 'ref_max': 'Bench Press','factor': 0.60},
        {'name': 'Push-ups (failure)', 'ref_max': None, 'factor': None}, # BW exercise
        {'name': 'Barbell Row', 'ref_max': 'Bench Press','factor': 0.80},
        {'name': 'DB Row', 'ref_max': 'Bench Press','factor': 0.40},
        {'name': 'Skullcrushers', 'ref_max': 'Bench Press','factor': 0.30},
        {'name': 'Cable Pushdowns', 'ref_max': 'Bench Press','factor': 0.25},
        {'name': 'Face Pulls', 'ref_max': 'Bench Press','factor': 0.20},
        {'name': 'Bicep Curls', 'ref_max': 'Bench Press','factor': 0.25},
        {'name': 'Pallof Press', 'ref_max': 'Bench Press','factor': 0.25},
        {'name': 'TRX Rows (failure)', 'ref_max': None, 'factor': None}, # BW exercise
    ],
    'Wednesday': [
        {'name': 'Deadlift', 'ref_max': 'Deadlift', 'factor': None}, # main lift
        {'name': 'Trap-Bar Deadlift', 'ref_max': 'Deadlift', 'factor': 0.90},
        {'name': 'Romanian Deadlift', 'ref_max': 'Deadlift', 'factor': 0.60},
        {'name': 'Single-Leg RDL', 'ref_max': 'Deadlift', 'factor': 0.35},
        {'name': 'Good Mornings', 'ref_max': 'Back Squat', 'factor': 0.40},
        {'name': 'Bulgarian Split Squat', 'ref_max': 'Back Squat', 'factor': 0.35},
        {'name': 'Leg Curl', 'ref_max': 'Deadlift', 'factor': 0.30},
        {'name': 'Reverse Hyperext (failure)', 'ref_max': None, 'factor': None}, # BW exercise
        {'name': 'Hanging Leg Raises (failure)', 'ref_max': None, 'factor': None},
    ],
    'Thursday': [
        {'name': 'Standing Military Press', 'ref_max': 'Shoulder Press','factor': None}, # main lift
        {'name': 'DB Shoulder Press', 'ref_max': 'Shoulder Press','factor': 0.75},
        {'name': 'Single-Arm Landmine Press', 'ref_max': 'Shoulder Press','factor': 0.60},
        {'name': 'Dead Arm Hang (failure)', 'ref_max': None, 'factor': None}, # BW exercise
        {'name': 'Lat Pulldown', 'ref_max': 'Bench Press', 'factor': 0.65},
        {'name': 'Lateral Raises', 'ref_max': 'Shoulder Press','factor': 0.35},
        {'name': 'Rear Delt Flyes', 'ref_max': 'Shoulder Press','factor': 0.35},
        {'name': 'Upright Rows', 'ref_max': 'Shoulder Press','factor': 0.35},
        {'name': 'Shrugs', 'ref_max': 'Deadlift', 'factor': 0.30},
        {'name': 'Pallof Press', 'ref_max': 'Bench Press', 'factor': 0.25},
    ],
}

# =========================
# HELPERS
# =========================

def parse_max(max_str):
    if pd.isna(max_str) or max_str == 'N/A' or max_str == '':
        return None
    max_str = str(max_str).strip()
    import re
    m = re.search(r'(\d+(?:\.\d+)?)', max_str)
    return float(m.group(1)) if m else None

def calculate_target_weight(max_weight, factor, round_to=5):
    if max_weight is None or factor is None:
        return None
    target = max_weight * factor
    return round(target / round_to) * round_to

def get_phase_intensity(phase_config, week_in_phase):
    min_i = phase_config['main_intensity_min']
    max_i = phase_config['main_intensity_max']
    rng = max_i - min_i
    prog = (week_in_phase - 1) / (phase_config['weeks'] - 1)
    return min_i + prog * rng

def get_accessory_reps(mesocycle):
    """Return rep range for accessories based on mesocycle."""
    return mesocycle['main_reps']

def load_athletes(filename):
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return []
    df = pd.read_csv(filename)
    athletes = []
    for _, row in df.iterrows():
        athletes.append({
            'name': row['Name'],
            'maxes': {
                'Back Squat': parse_max(row.get('Squat')), # CSV column name
                'Bench Press': parse_max(row.get('Bench Press')),
                'Deadlift': parse_max(row.get('Deadlift')),
                'Shoulder Press': parse_max(row.get('Shoulder Press')),
            }
        })
    return athletes

def build_bold_target(text_before_at, weight_str):
    """Return HTML string with weight/BW bolded after '@'."""
    # text_before_at is like "3×10 @"
    html = f"{text_before_at} <b>{weight_str}</b>"
    return html

def choose_phase_accessories_unique(phase_index, mesocycle):
    """
    Choose accessories for the whole phase with no repeats across days.
    Ensures one bodyweight exercise per day and guarantees specific exercises for Tuesday in Phase 1 & 2.
    Returns dict: day -> list of accessory dicts (number varies by day).
    """
    random.seed(100 + phase_index)
    phase_name = mesocycle['name']
    
    # Flat pool of all accessories tagged by day, excluding main lifts
    flat_pool = []
    for day, exercises in EXERCISE_POOLS.items():
        for e in exercises:
            if e['factor'] is None and e['ref_max'] in MAIN_LIFT_MAXES.values():
                continue # skip main lift entries
            flat_pool.append((day, e))
    
    # Shuffle to randomize global accessory order
    random.shuffle(flat_pool)
    
    per_day = {d: [] for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']}
    used_names = set()
    
    # First pass: add phase-specific guaranteed exercises and bodyweight exercises
    for day in per_day.keys():
        # For Tuesday in Phase 1 and Phase 2, add guaranteed exercises
        if day == 'Tuesday' and phase_name in ['Phase 1', 'Phase 2']:
            for guaranteed_ex in TUESDAY_PHASE_1_2_GUARANTEED:
                per_day[day].append(guaranteed_ex)
                used_names.add(guaranteed_ex['name'])
        else:
            # For all other days/phases, add one bodyweight exercise from the day's available pool
            if day in BODYWEIGHT_BY_DAY:
                available_bw = [e for day_tag, e in flat_pool 
                               if day_tag == day and e['name'] in BODYWEIGHT_BY_DAY[day] 
                               and e['name'] not in used_names]
                if available_bw:
                    bw_exercise = random.choice(available_bw)
                    per_day[day].append(bw_exercise)
                    used_names.add(bw_exercise['name'])
    
    # Second pass: fill remaining slots with random non-bodyweight exercises
    for day in per_day.keys():
        target_count = RANDOM_ACCESSORY_COUNT[day]
        
        # Count guaranteed exercises
        guaranteed_count = len(GUARANTEED_ACCESSORIES.get(day, []))
        if day == 'Tuesday' and phase_name in ['Phase 1', 'Phase 2']:
            guaranteed_count = len(TUESDAY_PHASE_1_2_GUARANTEED)
        
        # For Tuesday Phase 1 & 2, no random accessories needed (already at 4 total)
        if day == 'Tuesday' and phase_name in ['Phase 1', 'Phase 2']:
            continue
        
        bw_count = sum(1 for acc in per_day[day] if acc['name'] in BODYWEIGHT_EXERCISES)
        needed = target_count - guaranteed_count - bw_count
        
        for day_tag, ex in flat_pool:
            if day_tag != day:
                continue
            if ex['name'] in used_names:
                continue
            if ex['name'] in BODYWEIGHT_EXERCISES:
                continue  # Skip bodyweight exercises in this pass
            per_day[day].append(ex)
            used_names.add(ex['name'])
            if len(per_day[day]) >= target_count:
                break
    
    # Fallback: if any day still needs exercises, allow repeats
    for day in per_day.keys():
        target_count = RANDOM_ACCESSORY_COUNT[day]
        while len(per_day[day]) < target_count:
            remaining = [ex for d, ex in flat_pool if d == day]
            if not remaining:
                break
            ex = random.choice(remaining)
            per_day[day].append(ex)
    
    return per_day

# =========================
# PDF BUILDING
# =========================

def build_phase_pdf(athlete, mesocycle):
    phase_name = mesocycle['name']
    phase_start = mesocycle['start_date']
    weeks = mesocycle['weeks']
    phase_end = phase_start + timedelta(days=weeks * 7 - 1)
    
    safe_name = athlete['name'].replace(' ', '_')
    athlete_dir = os.path.join(OUTPUT_DIR, safe_name)
    os.makedirs(athlete_dir, exist_ok=True)
    
    pdf_filename = os.path.join(
        athlete_dir,
        f"{safe_name}_{phase_name.replace(' ', '')}.pdf"
    )
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=landscape(letter),
        topMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ---------- HEADER ----------
    
    if os.path.exists(LOGO_FILE):
        left_logo = Image(LOGO_FILE, width=1.0*inch, height=1.0*inch)
        right_logo = Image(LOGO_FILE, width=1.0*inch, height=1.0*inch)
    else:
        left_logo = Paragraph(" ", styles['Normal'])
        right_logo = Paragraph(" ", styles['Normal'])
    
    title_style = ParagraphStyle(
        'TitleLarge',
        parent=styles['Heading1'],
        fontSize=20,
        leading=22,
        alignment=1,
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    
    date_range_str = f"{phase_start.strftime('%b %d')} – {phase_end.strftime('%b %d, %Y')}"
    info_text = f"{athlete['name']} | {phase_name} | {date_range_str}"
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        alignment=1,
        fontName='Helvetica-Bold',
    )
    
    center_cell = [
        Paragraph("PHS FOOTBALL POWER PROGRAM", title_style),
        Paragraph(info_text, info_style),
    ]
    
    header_row = [[left_logo, center_cell, right_logo]]
    header_table = Table(
        header_row,
        colWidths=[2.0*inch, 5.7*inch, 2.0*inch],
        rowHeights=[1.10*inch],
    )
    
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0, colors.white),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.4*inch))
    
    # ---------- MAIN TABLE ----------
    
    header = [
        'EXERCISES',
        'WEEK 1 TARGET', 'REPS',
        'WEEK 2 TARGET', 'REPS',
        'WEEK 3 TARGET', 'REPS',
        'WEEK 4 TARGET', 'REPS',
    ]
    
    table_data = [header]
    
    # Unique accessories per phase, no repeats across days
    phase_index = MESOCYCLES.index(mesocycle)
    phase_accessories = choose_phase_accessories_unique(phase_index, mesocycle)
    
    day_row_ranges = []
    row_idx = 1
    
    day_order = [
        ('Monday', 'MONDAY'),
        ('Tuesday', 'TUESDAY'),
        ('Wednesday', 'WEDNESDAY'),
        ('Thursday', 'THURSDAY'),
    ]
    
    for day_name, day_label in day_order:
        # Day bar row
        day_bar = [day_label] + [''] * (len(header) - 1)
        table_data.append(day_bar)
        bar_idx = row_idx
        row_idx += 1
        start_idx = row_idx
        
        # Main lift row
        main_lift = MAIN_LIFTS[day_name]
        max_key = MAIN_LIFT_MAXES[main_lift]
        main_max = athlete['maxes'].get(max_key)
        
        main_row = [main_lift]
        for wk in range(1, weeks + 1):
            intensity = get_phase_intensity(mesocycle, wk)
            if main_max:
                tw = calculate_target_weight(main_max, intensity)
                txt = build_bold_target(
                    f"{mesocycle['main_sets']}×{mesocycle['main_reps']} @",
                    f"{int(tw)} lbs"
                )
            else:
                txt = f"{mesocycle['main_sets']}×{mesocycle['main_reps']} @ ______"
            main_row.extend([txt, ""])
        
        table_data.append(main_row)
        row_idx += 1
        
        # Accessory rows with phase-aware intensity, reps, and progression
        accessory_reps = get_accessory_reps(mesocycle)
        
        # First, add guaranteed accessories if they exist for this day
        guaranteed_accs = GUARANTEED_ACCESSORIES.get(day_name, [])
        for acc in guaranteed_accs:
            name = acc['name']
            acc_row = [name]
            for wk in range(1, weeks + 1):
                if acc['ref_max'] and acc['factor']:
                    ref_max = athlete['maxes'].get(acc['ref_max'])
                    if ref_max:
                        # For Push Press: apply phase intensity to the training weight
                        if acc.get('is_push_press'):
                            # Push Press: 115% of strict press training weight with progression
                            strict_press_intensity = get_phase_intensity(mesocycle, wk)
                            strict_press_training = calculate_target_weight(ref_max, strict_press_intensity, round_to=5)
                            # Push press is 115% of that training weight
                            tw = calculate_target_weight(strict_press_training, 1.15, round_to=5)
                        else:
                            # Standard accessory calculation
                            acc_intensity = ACCESSORY_INTENSITY[phase_index]
                            adjusted_factor = acc['factor'] * acc_intensity
                            phase_progression = get_phase_intensity(mesocycle, wk)
                            final_factor = adjusted_factor * (phase_progression / ACCESSORY_INTENSITY[phase_index])
                            tw = calculate_target_weight(ref_max, final_factor, round_to=5)
                        txt = build_bold_target(f"{mesocycle['main_sets']}×{accessory_reps} @", f"{int(tw)} lbs")
                    else:
                        txt = f"{mesocycle['main_sets']}×{accessory_reps} @ ______"
                else:
                    txt = f"{mesocycle['main_sets']}×{accessory_reps} @ ______"
                acc_row.extend([txt, ""])
            table_data.append(acc_row)
            row_idx += 1
        
        # Then add random accessories for this day
        for acc in phase_accessories[day_name]:
            name = acc['name']
            acc_row = [name]
            for wk in range(1, weeks + 1):
                if name in BODYWEIGHT_EXERCISES:
                    # Bodyweight exercises don't scale with weight progression
                    txt = "3 sets @ BW"
                elif acc['ref_max'] and acc['factor']:
                    ref_max = athlete['maxes'].get(acc['ref_max'])
                    if ref_max:
                        # Standard accessory: apply phase intensity multiplier and within-phase progression
                        acc_intensity = ACCESSORY_INTENSITY[phase_index]
                        adjusted_factor = acc['factor'] * acc_intensity
                        # Apply within-phase intensity progression like main lifts
                        phase_progression = get_phase_intensity(mesocycle, wk)
                        final_factor = adjusted_factor * (phase_progression / ACCESSORY_INTENSITY[phase_index])
                        tw = calculate_target_weight(ref_max, final_factor, round_to=5)
                        txt = build_bold_target(f"{mesocycle['main_sets']}×{accessory_reps} @", f"{int(tw)} lbs")
                    else:
                        txt = f"{mesocycle['main_sets']}×{accessory_reps} @ ______"
                else:
                    # No ref_max or factor - bodyweight or unweighted
                    txt = f"{mesocycle['main_sets']} sets @ ______"
                acc_row.extend([txt, ""])
            table_data.append(acc_row)
            row_idx += 1
        
        end_idx = row_idx - 1
        day_row_ranges.append((bar_idx, start_idx, end_idx))
    
    normal_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        alignment=1,
    )
    
    for r in range(1, len(table_data)):
        row = table_data[r]
        for c in range(1, len(row), 2): # target columns only
            val = row[c]
            if isinstance(val, str) and '@' in val:
                row[c] = Paragraph(val, normal_style)
    
    # Column widths
    col_widths = [
        1.8*inch,
        1.3*inch, 0.8*inch,
        1.3*inch, 0.8*inch,
        1.3*inch, 0.8*inch,
        1.3*inch, 0.8*inch,
    ]
    
    # Row heights
    row_heights = [0.30*inch] # header
    for bar_idx, start_idx, end_idx in day_row_ranges:
        while len(row_heights) < bar_idx:
            row_heights.append(0.30*inch)
        row_heights.append(0.25*inch) # day bar
        for _ in range(start_idx, end_idx + 1):
            row_heights.append(0.30*inch)
    while len(row_heights) < len(table_data):
        row_heights.append(0.30*inch)
    
    main_table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
    
    base_style = [
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BLACK),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Main header row: dark gold
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLACK),
        # Body font
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        # Bold exercise names
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]
    
    for bar_idx, start_idx, end_idx in day_row_ranges:
        base_style.extend([
            ('BACKGROUND', (0, bar_idx), (-1, bar_idx), COLOR_BLACK),
            ('FONTNAME', (0, bar_idx), (-1, bar_idx), 'Helvetica-Bold'),
            ('FONTSIZE', (0, bar_idx), (-1, bar_idx), 9),
            ('TEXTCOLOR', (0, bar_idx), (-1, bar_idx), colors.white),
        ])
        
        toggle = True
        for r in range(start_idx, end_idx + 1):
            bg = ROW_BG_LIGHT if toggle else ROW_BG_MED
            base_style.append(
                ('BACKGROUND', (0, r), (-1, r), bg)
            )
            toggle = not toggle
    
    main_table.setStyle(TableStyle(base_style))
    story.append(main_table)
    
    doc.build(story)
    print(f" → {pdf_filename}")


def build_blank_phase_pdf(mesocycle):
    """
    Build a blank workout sheet with exercise names but no calculated weights.
    Athletes can fill in their own weights.
    """
    phase_name = mesocycle['name']
    phase_start = mesocycle['start_date']
    weeks = mesocycle['weeks']
    phase_end = phase_start + timedelta(days=weeks * 7 - 1)
    
    blank_dir = os.path.join(OUTPUT_DIR, 'BLANK_SHEETS')
    os.makedirs(blank_dir, exist_ok=True)
    
    pdf_filename = os.path.join(
        blank_dir,
        f"BLANK_{phase_name.replace(' ', '')}.pdf"
    )
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=landscape(letter),
        topMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ---------- HEADER ----------
    
    if os.path.exists(LOGO_FILE):
        left_logo = Image(LOGO_FILE, width=1.0*inch, height=1.0*inch)
        right_logo = Image(LOGO_FILE, width=1.0*inch, height=1.0*inch)
    else:
        left_logo = Paragraph(" ", styles['Normal'])
        right_logo = Paragraph(" ", styles['Normal'])
    
    title_style = ParagraphStyle(
        'TitleLarge',
        parent=styles['Heading1'],
        fontSize=20,
        leading=22,
        alignment=1,
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    
    date_range_str = f"{phase_start.strftime('%b %d')} – {phase_end.strftime('%b %d, %Y')}"
    info_text = f"ATHLETE NAME: ________________ | {phase_name} | {date_range_str}"
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        alignment=1,
        fontName='Helvetica-Bold',
    )
    
    center_cell = [
        Paragraph("PHS FOOTBALL POWER PROGRAM", title_style),
        Paragraph(info_text, info_style),
    ]
    
    header_row = [[left_logo, center_cell, right_logo]]
    header_table = Table(
        header_row,
        colWidths=[2.0*inch, 5.7*inch, 2.0*inch],
        rowHeights=[1.10*inch],
    )
    
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0, colors.white),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.4*inch))
    
    # ---------- MAIN TABLE ----------
    
    header = [
        'EXERCISES',
        'WEEK 1 TARGET', 'REPS',
        'WEEK 2 TARGET', 'REPS',
        'WEEK 3 TARGET', 'REPS',
        'WEEK 4 TARGET', 'REPS',
    ]
    
    table_data = [header]
    
    # Get the same exercise structure as athlete sheets (use phase index 0 for blank structure)
    phase_index = MESOCYCLES.index(mesocycle)
    phase_accessories = choose_phase_accessories_unique(phase_index, mesocycle)
    
    day_row_ranges = []
    row_idx = 1
    
    day_order = [
        ('Monday', 'MONDAY'),
        ('Tuesday', 'TUESDAY'),
        ('Wednesday', 'WEDNESDAY'),
        ('Thursday', 'THURSDAY'),
    ]
    
    for day_name, day_label in day_order:
        # Day bar row
        day_bar = [day_label] + [''] * (len(header) - 1)
        table_data.append(day_bar)
        bar_idx = row_idx
        row_idx += 1
        start_idx = row_idx
        
        # Main lift row
        main_lift = MAIN_LIFTS[day_name]
        main_row = [main_lift]
        for wk in range(1, weeks + 1):
            txt = f"{mesocycle['main_sets']}×{mesocycle['main_reps']} @ ______"
            main_row.extend([txt, ""])
        
        table_data.append(main_row)
        row_idx += 1
        
        # Accessory rows
        accessory_reps = get_accessory_reps(mesocycle)
        
        # First, add guaranteed accessories if they exist for this day
        guaranteed_accs = GUARANTEED_ACCESSORIES.get(day_name, [])
        for acc in guaranteed_accs:
            name = acc['name']
            acc_row = [name]
            for wk in range(1, weeks + 1):
                txt = f"{mesocycle['main_sets']}×{accessory_reps} @ ______"
                acc_row.extend([txt, ""])
            table_data.append(acc_row)
            row_idx += 1
        
        # Then add random accessories for this day
        for acc in phase_accessories[day_name]:
            name = acc['name']
            acc_row = [name]
            for wk in range(1, weeks + 1):
                if name in BODYWEIGHT_EXERCISES:
                    txt = "3 sets @ BW"
                else:
                    txt = f"{mesocycle['main_sets']}×{accessory_reps} @ ______"
                acc_row.extend([txt, ""])
            table_data.append(acc_row)
            row_idx += 1
        
        end_idx = row_idx - 1
        day_row_ranges.append((bar_idx, start_idx, end_idx))
    
    normal_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        alignment=1,
    )
    
    for r in range(1, len(table_data)):
        row = table_data[r]
        for c in range(1, len(row), 2): # target columns only
            val = row[c]
            if isinstance(val, str):
                row[c] = Paragraph(val, normal_style)
    
    # Column widths
    col_widths = [
        1.8*inch,
        1.3*inch, 0.8*inch,
        1.3*inch, 0.8*inch,
        1.3*inch, 0.8*inch,
        1.3*inch, 0.8*inch,
    ]
    
    # Row heights
    row_heights = [0.30*inch] # header
    for bar_idx, start_idx, end_idx in day_row_ranges:
        while len(row_heights) < bar_idx:
            row_heights.append(0.30*inch)
        row_heights.append(0.25*inch) # day bar
        for _ in range(start_idx, end_idx + 1):
            row_heights.append(0.30*inch)
    while len(row_heights) < len(table_data):
        row_heights.append(0.30*inch)
    
    main_table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
    
    base_style = [
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BLACK),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Main header row: dark gold
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLACK),
        # Body font
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        # Bold exercise names
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]
    
    for bar_idx, start_idx, end_idx in day_row_ranges:
        base_style.extend([
            ('BACKGROUND', (0, bar_idx), (-1, bar_idx), COLOR_BLACK),
            ('FONTNAME', (0, bar_idx), (-1, bar_idx), 'Helvetica-Bold'),
            ('FONTSIZE', (0, bar_idx), (-1, bar_idx), 9),
            ('TEXTCOLOR', (0, bar_idx), (-1, bar_idx), colors.white),
        ])
        
        toggle = True
        for r in range(start_idx, end_idx + 1):
            bg = ROW_BG_LIGHT if toggle else ROW_BG_MED
            base_style.append(
                ('BACKGROUND', (0, r), (-1, r), bg)
            )
            toggle = not toggle
    
    main_table.setStyle(TableStyle(base_style))
    story.append(main_table)
    
    doc.build(story)
    print(f" → {pdf_filename}")

# =========================
# MAIN
# =========================

def main():
    print("\n=== PHS FOOTBALL POWER PROGRAM Workout Sheet Generator ===\n")
    
    athletes = load_athletes(TESTING_DATA_FILE)
    if not athletes:
        print("No athletes found. Exiting.")
        return
    
    print(f"Loaded {len(athletes)} athlete(s).\n")
    
    for athlete in athletes:
        print(f"Generating workouts for {athlete['name']}...")
        print(f" Maxes: BackSq={athlete['maxes']['Back Squat']}, "
              f"BP={athlete['maxes']['Bench Press']}, "
              f"DL={athlete['maxes']['Deadlift']}, "
              f"OHP={athlete['maxes']['Shoulder Press']}")
        for meso in MESOCYCLES:
            build_phase_pdf(athlete, meso)
        print()
    
    # Generate blank sheets for each phase
    print("Generating blank sheets for new athletes...\n")
    for meso in MESOCYCLES:
        print(f"Generating blank {meso['name']} sheet...")
        build_blank_phase_pdf(meso)
    
    print("\n✓ Complete!")

if __name__ == '__main__':
    main()
