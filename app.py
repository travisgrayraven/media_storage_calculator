import ipywidgets as widgets
from IPython.display import display, HTML, Javascript
import json

# --- Constants and Assumptions ---
USABLE_CAPACITY_FACTOR = 0.931 # Accounts for GB (10^9) vs GiB (2^30) and filesystem overhead
AUDIO_BITRATE_MBPS = 0.064 # 64 kbps for a single AAC audio track

# --- DATA MAPS FOR GRANULAR CONTROL ---
# H.265 Bitrate estimations (Mbps)
H265_BITRATE_MAP = {
    "1080p": {"30": 4.5, "15": 2.5, "10": 1.8, "5": 1.2},
    "720p":  {"30": 3.0, "15": 1.5, "10": 1.0, "5": 0.7},
    "540p":  {"30": 2.2, "15": 1.2, "10": 0.9, "5": 0.6},
    "480p":  {"30": 1.5, "15": 0.9, "10": 0.7, "5": 0.5},
    "360p":  {"30": 1.0, "15": 0.6, "10": 0.5, "5": 0.4},
    "180p":  {"15": 0.4, "10": 0.3, "5": 0.2}
}

# H.264 bitrates estimated at ~1.7x the H.265 rates
H264_BITRATE_MAP = {
    "1080p": {"30": 7.5, "15": 4.2, "10": 3.0, "5": 2.0},
    "720p":  {"30": 5.0, "15": 2.5, "10": 1.7, "5": 1.2},
    "540p":  {"30": 3.7, "15": 2.0, "10": 1.5, "5": 1.0},
    "480p":  {"30": 2.5, "15": 1.5, "10": 1.2, "5": 0.8},
    "360p":  {"30": 1.7, "15": 1.0, "10": 0.8, "5": 0.7},
    "180p":  {"15": 0.7, "10": 0.5, "5": 0.4}
}

# --- ADDED: Missing map for JPEG frame sizes (estimates in KB) ---
# This was missing from the original code and is required for the "Compressed JPEGs" calculation.
FRAME_SIZE_MAP = {
    "1080p": 150, "720p": 100, "540p": 70, "480p": 50, "360p": 30, "180p": 15
}


# --- Widget Creation ---
title_style = '<style>h2 { margin-bottom: 5px; margin-top: 15px; } p {margin-top: 2px; color: #666;} .widget-label {min-width: 130px !important;}</style>'
main_title = widgets.HTML(f'{title_style}<h1>Raven Storage Calculator</h1>')

# Storage and Codec Layout
storage_config_title = widgets.HTML('<h2>Storage Configuration</h2>')
w_storage_size = widgets.Dropdown(options=[32, 64, 128, 256, 512, 1024], value=256, description="Card Size (GB):")
w_real_capacity_label = widgets.Label(value="")
w_codec_select = widgets.Dropdown(options=["H.265", "H.264"], value="H.265", description="Codec:")
storage_box = widgets.VBox([w_storage_size, w_real_capacity_label], layout=widgets.Layout(align_items='flex-start'))
codec_box = widgets.VBox([w_codec_select], layout=widgets.Layout(padding='0 0 0 50px'))
storage_config_box = widgets.HBox([storage_box, codec_box])

# Video Folder Widgets
video_config_title = widgets.HTML('<h2>Video Folder Configuration</h2>')
w_video_cam_select = widgets.Dropdown(options=["Both", "Road Only", "Cabin Only", "None"], value="Both", description="Enabled Cameras:")
w_video_audio = widgets.Checkbox(value=False, description="Audio", indent=False)
w_road_res = widgets.Dropdown(options=["1080p", "720p", "540p", "480p", "360p"], value="1080p", description="Road Res:")
w_road_fps = widgets.Dropdown(options=["30", "15", "10"], value="30", description="Road FPS:")
w_cabin_res = widgets.Dropdown(options=["720p", "540p", "480p", "360p", "180p"], value="720p", description="Cabin Res:")
w_cabin_fps = widgets.Dropdown(options=["15", "10", "5"], value="15", description="Cabin FPS:")
video_col1 = widgets.VBox([w_video_cam_select, w_road_res, w_road_fps])
video_col2 = widgets.VBox([w_video_audio, w_cabin_res, w_cabin_fps])
video_config_box = widgets.HBox([video_col1, video_col2])
w_video_bitrate_display = widgets.HTML(value="")

# Timelapse Folder Widgets
timelapse_config_title = widgets.HTML('<h2>Timelapse Folder Configuration</h2>')
w_timelapse_format = widgets.Dropdown(options=["MP4", "Compressed JPEGs"], value="MP4", description="Storage Format:")
w_timelapse_cam = widgets.Dropdown(options=["Both", "Road Only", "Cabin Only", "None"], value="Both", description="Enabled Cameras:")
w_timelapse_audio = widgets.Checkbox(value=False, description="Audio", indent=False)
# --- MODIFIED: Frame interval slider min and step values changed ---
w_timelapse_interval = widgets.FloatSlider(value=1.0, min=0.1, max=300, step=0.1, description="Frame Interval (s):", readout_format='.1f')
w_timelapse_fps_label = widgets.Label(value="")
w_timelapse_road_res = widgets.Dropdown(options=["1080p", "720p", "540p", "480p", "360p"], value="360p", description="Road Res:")
w_timelapse_cabin_res = widgets.Dropdown(options=["720p", "540p", "480p", "360p", "180p"], value="180p", description="Cabin Res:")
timelapse_col1 = widgets.VBox([w_timelapse_format, w_timelapse_cam, w_timelapse_road_res, w_timelapse_interval])
timelapse_col2 = widgets.VBox([widgets.Label(), w_timelapse_audio, w_timelapse_cabin_res, w_timelapse_fps_label]) # Added label for spacing
timelapse_config_box = widgets.HBox([timelapse_col1, timelapse_col2])
w_timelapse_bitrate_display = widgets.HTML(value="")

# Storage and Usage Widgets
usage_title = widgets.HTML('<h2>Storage Allocation & Vehicle Usage</h2>')
w_video_hours = widgets.FloatSlider(value=60, min=0, max=1000, step=1, description="Video Hours:", readout_format='.1f')
w_timelapse_hours = widgets.FloatSlider(value=1000, min=0, max=10000, step=10, description="Timelapse Hours:", readout_format='.0f')
w_hours_per_day = widgets.IntSlider(value=8, min=1, max=24, step=1, description="Hrs Driven/Day:")
w_days_per_week = widgets.IntSlider(value=5, min=1, max=7, step=1, description="Days Driven/Wk:")
usage_box1 = widgets.HBox([w_video_hours, w_timelapse_hours])
usage_box2 = widgets.HBox([w_hours_per_day, w_days_per_week])

# Output Widgets & Print Button
results_title = widgets.HTML('<hr><h2>Calculation Results</h2>')
output_video = widgets.HTML(value="")
output_timelapse = widgets.HTML(value="")
results_box = widgets.HBox([output_video, output_timelapse])
output_lookback = widgets.HTML(value="")
# --- CONFIRMED: Print button text color is set to white ---
w_print_button = widgets.Button(description="Print", style={'button_color': 'royalblue', 'text_color': 'white'}, layout=widgets.Layout(margin='15px 0 0 0'))

# --- Main App Container ---
main_container = widgets.VBox([
    main_title,
    storage_config_title, storage_config_box,
    video_config_title, video_config_box, w_video_bitrate_display,
    timelapse_config_title, timelapse_config_box, w_timelapse_bitrate_display,
    usage_title, usage_box1, usage_box2,
    results_title, results_box, output_lookback, w_print_button
], layout=widgets.Layout(margin='20px 0 0 20px'))

# --- Calculation and Update Logic ---
updating_from_code = False

def get_low_fps_bitrate(resolution, fps, bitrate_map):
    lowest_fps_in_map = min([int(k) for k in bitrate_map[resolution].keys()])
    if str(int(fps)) in bitrate_map[resolution]: return bitrate_map[resolution][str(int(fps))]
    elif fps < lowest_fps_in_map: return (bitrate_map[resolution][str(lowest_fps_in_map)] / lowest_fps_in_map) * fps
    else: return bitrate_map[resolution][str(lowest_fps_in_map)]

def calculate_and_update(change):
    global updating_from_code
    if updating_from_code: return

    usable_storage_gb = w_storage_size.value * USABLE_CAPACITY_FACTOR
    w_real_capacity_label.value = f"({usable_storage_gb:.1f} GB Usable)"

    video_col2.layout.visibility = 'visible' if w_video_cam_select.value in ["Both", "Cabin Only"] else 'hidden'
    w_road_res.layout.visibility = 'visible' if w_video_cam_select.value in ["Both", "Road Only"] else 'hidden'
    w_road_fps.layout.visibility = 'visible' if w_video_cam_select.value in ["Both", "Road Only"] else 'hidden'
    
    timelapse_col2.layout.visibility = 'visible' if w_timelapse_cam.value in ["Both", "Cabin Only"] else 'hidden'
    w_timelapse_road_res.layout.visibility = 'visible' if w_timelapse_cam.value in ["Both", "Road Only"] else 'hidden'

    w_timelapse_audio.disabled = (w_timelapse_format.value == "Compressed JPEGs")
    if w_timelapse_audio.disabled: w_timelapse_audio.value = False

    BITRATE_MAP = H265_BITRATE_MAP if w_codec_select.value == "H.265" else H264_BITRATE_MAP
    
    road_bitrate, cabin_bitrate, audio_bitrate = 0, 0, 0
    if w_video_cam_select.value in ["Both", "Road Only"]: road_bitrate = BITRATE_MAP[w_road_res.value][w_road_fps.value]
    if w_video_cam_select.value in ["Both", "Cabin Only"]: cabin_bitrate = BITRATE_MAP[w_cabin_res.value][w_cabin_fps.value]
    if w_video_audio.value:
        if w_video_cam_select.value == "Both": audio_bitrate = AUDIO_BITRATE_MBPS * 2
        elif w_video_cam_select.value != "None": audio_bitrate = AUDIO_BITRATE_MBPS
    total_video_bitrate_mbps = road_bitrate + cabin_bitrate + audio_bitrate
    gb_per_hour_video = (total_video_bitrate_mbps * 3600) / (8 * 1024) if total_video_bitrate_mbps > 0 else 0
    if total_video_bitrate_mbps > 0: w_video_bitrate_display.value = f"<p><i>Est. Bitrate ({w_codec_select.value}): Road ({road_bitrate:.2f}) + Cabin ({cabin_bitrate:.2f}) + Audio ({audio_bitrate:.3f}) = <b>{total_video_bitrate_mbps:.3f} Mbps</b></i></p>"
    else: w_video_bitrate_display.value = ""

    gb_per_hour_timelapse = 0
    
    # --- MODIFIED: FPS label now includes distance calculation ---
    timelapse_fps = 1 / w_timelapse_interval.value
    # Speed of 100 km/hr is ~27.78 m/s. Distance = speed (m/s) * time between frames (s)
    distance_per_frame = (100 * 1000 / 3600) * w_timelapse_interval.value
    w_timelapse_fps_label.value = f"({timelapse_fps:.2f} FPS ~ {distance_per_frame:.1f}m @ 100km/hr)"
    
    if w_timelapse_format.value == "MP4":
        w_timelapse_bitrate_display.layout.visibility = 'visible'
        timelapse_road_bitrate, timelapse_cabin_bitrate, timelapse_audio_bitrate = 0, 0, 0
        if w_timelapse_cam.value in ["Both", "Road Only"]: timelapse_road_bitrate = get_low_fps_bitrate(w_timelapse_road_res.value, timelapse_fps, BITRATE_MAP)
        if w_timelapse_cam.value in ["Both", "Cabin Only"]: timelapse_cabin_bitrate = get_low_fps_bitrate(w_timelapse_cabin_res.value, timelapse_fps, BITRATE_MAP)
        if w_timelapse_audio.value:
            if w_timelapse_cam.value == "Both": timelapse_audio_bitrate = AUDIO_BITRATE_MBPS * 2
            elif w_timelapse_cam.value != "None": timelapse_audio_bitrate = AUDIO_BITRATE_MBPS
        total_timelapse_bitrate_mbps = timelapse_road_bitrate + timelapse_cabin_bitrate + timelapse_audio_bitrate
        gb_per_hour_timelapse = (total_timelapse_bitrate_mbps * 3600) / (8 * 1024) if total_timelapse_bitrate_mbps > 0 else 0
        if total_timelapse_bitrate_mbps > 0: w_timelapse_bitrate_display.value = f"<p><i>Est. Bitrate ({w_codec_select.value}): Road ({timelapse_road_bitrate:.2f}) + Cabin ({timelapse_cabin_bitrate:.2f}) + Audio ({timelapse_audio_bitrate:.3f}) = <b>{total_timelapse_bitrate_mbps:.3f} Mbps</b></i></p>"
        else: w_timelapse_bitrate_display.value = ""
    else: # Compressed JPEGs
        w_timelapse_bitrate_display.layout.visibility = 'hidden'
        kb_per_hour_timelapse = 0
        frames_per_hour = 3600 / w_timelapse_interval.value
        if w_timelapse_cam.value in ["Both", "Road Only"]: kb_per_hour_timelapse += frames_per_hour * FRAME_SIZE_MAP[w_timelapse_road_res.value]
        if w_timelapse_cam.value in ["Both", "Cabin Only"]: kb_per_hour_timelapse += frames_per_hour * FRAME_SIZE_MAP[w_timelapse_cabin_res.value]
        gb_per_hour_timelapse = kb_per_hour_timelapse / (1024 * 1024) if kb_per_hour_timelapse > 0 else 0

    updating_from_code = True
    max_video_hours = usable_storage_gb / gb_per_hour_video if gb_per_hour_video > 0 else 0
    max_timelapse_hours = usable_storage_gb / gb_per_hour_timelapse if gb_per_hour_timelapse > 0 else 0
    if w_video_hours.value > max_video_hours: w_video_hours.value = max_video_hours
    w_video_hours.max = max_video_hours if max_video_hours > 1 else 1
    if w_timelapse_hours.value > max_timelapse_hours: w_timelapse_hours.value = max_timelapse_hours
    w_timelapse_hours.max = max_timelapse_hours if max_timelapse_hours > 1 else 1
    
    video_gb, timelapse_gb = 0, 0
    trigger_widget = change.get('owner', w_video_hours)
    if gb_per_hour_video == 0 and gb_per_hour_timelapse == 0: video_gb, timelapse_gb = 0, 0
    elif gb_per_hour_timelapse == 0: video_gb, timelapse_gb = usable_storage_gb, 0
    elif gb_per_hour_video == 0: timelapse_gb, video_gb = usable_storage_gb, 0
    else:
        if trigger_widget == w_video_hours: video_gb = gb_per_hour_video * w_video_hours.value
        elif trigger_widget == w_timelapse_hours: video_gb = usable_storage_gb - (gb_per_hour_timelapse * w_timelapse_hours.value)
        else: video_gb = gb_per_hour_video * w_video_hours.value
        if video_gb > usable_storage_gb: video_gb = usable_storage_gb
        elif video_gb < 0: video_gb = 0
        timelapse_gb = usable_storage_gb - video_gb
    w_video_hours.value = video_gb / gb_per_hour_video if gb_per_hour_video > 0 else 0
    w_timelapse_hours.value = timelapse_gb / gb_per_hour_timelapse if gb_per_hour_timelapse > 0 else 0
    updating_from_code = False
    
    final_video_gb = gb_per_hour_video * w_video_hours.value if gb_per_hour_video > 0 else 0
    final_timelapse_gb = gb_per_hour_timelapse * w_timelapse_hours.value if gb_per_hour_timelapse > 0 else 0

    hours_driven_per_week = w_hours_per_day.value * w_days_per_week.value
    video_lookback_weeks = w_video_hours.value / hours_driven_per_week if hours_driven_per_week > 0 else 0
    video_lookback_days = video_lookback_weeks * w_days_per_week.value
    video_lookback_months = video_lookback_weeks / 4.345
    video_lookback_years = video_lookback_months / 12
    timelapse_lookback_weeks = w_timelapse_hours.value / hours_driven_per_week if hours_driven_per_week > 0 else 0
    timelapse_lookback_days = timelapse_lookback_weeks * w_days_per_week.value
    timelapse_lookback_months = timelapse_lookback_weeks / 4.345
    timelapse_lookback_years = timelapse_lookback_months / 12

    output_video.value = f'<div style="padding-right: 20px; border-right: 1px solid #ccc; min-width: 250px;"><b>Video Folder:</b><br>' \
                          f'&nbsp;&nbsp;Storage Size: <b>{final_video_gb:.1f} GB</b><br>' \
                          f'&nbsp;&nbsp;Total Recording Time: <b>{w_video_hours.value:.1f} hours</b></div>'
    output_timelapse.value = f'<div style="padding-left: 50px; min-width: 250px;"><b>Timelapse Folder:</b><br>' \
                              f'&nbsp;&nbsp;Storage Size: <b>{final_timelapse_gb:.1f} GB</b><br>' \
                              f'&nbsp;&nbsp;Total Recording Time: <b>{w_timelapse_hours.value:.1f} hours</b></div>'
    output_lookback.value = f"<b>Estimated Lookback Period (based on usage profile):</b><br>" \
                             f"&nbsp;&nbsp;<b>Videos Folder:</b> {w_video_hours.value:.1f} hours | {video_lookback_days:.1f} driving days | {video_lookback_weeks:.1f} weeks | {video_lookback_months:.1f} months | {video_lookback_years:.2f} years<br>" \
                             f"&nbsp;&nbsp;<b>Timelapse Folder:</b> {w_timelapse_hours.value:.1f} hours | {timelapse_lookback_days:.1f} driving days | {timelapse_lookback_weeks:.1f} weeks | {timelapse_lookback_months:.1f} months | {timelapse_lookback_years:.2f} years"

# --- Function to generate printable report ---
def on_print_button_clicked(b):
    timelapse_audio_html = f"<p><b>Audio Enabled:</b> {w_timelapse_audio.value}</p>" if w_timelapse_format.value == 'MP4' else ""
    timelapse_settings_html = ""
    # --- MODIFIED: Report now uses the full FPS/distance label ---
    if w_timelapse_format.value == "MP4":
        timelapse_settings_html = f"<p><b>Interval:</b> {w_timelapse_interval.value}s {w_timelapse_fps_label.value}</p>" + w_timelapse_bitrate_display.value
    else:
        timelapse_settings_html = f"<p><b>Interval:</b> {w_timelapse_interval.value}s {w_timelapse_fps_label.value}</p>"
        
    settings_html = f"""
        <h2>Configuration Summary</h2>
        <p><b>Card Size:</b> {w_storage_size.value} GB ({w_storage_size.value * USABLE_CAPACITY_FACTOR:.1f} GB Usable)</p>
        <h3>Video Folder</h3>
        <p><b>Codec:</b> {w_codec_select.value}</p>
        <p><b>Enabled Cameras:</b> {w_video_cam_select.value}</p>
        <p><b>Audio:</b> {w_video_audio.value}</p>
        <p><b>Road Camera:</b> {w_road_res.value} @ {w_road_fps.value} FPS</p>
        <p><b>Cabin Camera:</b> {w_cabin_res.value} @ {w_cabin_fps.value} FPS</p>
        {w_video_bitrate_display.value}
        <h3>Timelapse Folder</h3>
        <p><b>Storage Format:</b> {w_timelapse_format.value}</p>
        <p><b>Enabled Cameras:</b> {w_timelapse_cam.value}</p>
        {timelapse_audio_html}
        <p><b>Road Resolution:</b> {w_timelapse_road_res.value}</p>
        <p><b>Cabin Resolution:</b> {w_timelapse_cabin_res.value}</p>
        {timelapse_settings_html}
        <h3>Vehicle Usage</h3>
        <p><b>Driving Schedule:</b> {w_hours_per_day.value} hours/day, {w_days_per_week.value} days/week</p>"""
    results_html = f"""
        <hr><h2>Calculated Results</h2>
        <table width="100%"><tr>
        <td style="vertical-align:top; padding-right:15px; border-right: 1px solid #ccc;">{output_video.value}</td>
        <td style="vertical-align:top; padding-left:15px;">{output_timelapse.value}</td>
        </tr></table><br>{output_lookback.value}"""
    full_report_html = f"""<html><head><title>Raven Storage Calculation Report</title>
    <style>body{{font-family: sans-serif;}} h2{{border-bottom: 1px solid #ccc; padding-bottom: 5px;}} table{{border-collapse: collapse;}} td{{vertical-align: top;}}</style>
    </head><body><h1>Raven Storage Calculation Report</h1>{settings_html}{results_html}</body></html>"""
    js_string = json.dumps(full_report_html)
    js_code = f"var win=window.open('','_blank');win.document.write({js_string});win.document.close();win.focus();setTimeout(()=>{{win.print();}},500);"
    display(Javascript(js_code))

# --- Observers ---
controls = [
    w_storage_size, w_codec_select, w_video_cam_select, w_video_audio, w_road_res, w_road_fps, w_cabin_res, w_cabin_fps,
    w_timelapse_cam, w_timelapse_format, w_timelapse_audio, w_timelapse_interval, w_timelapse_road_res, w_timelapse_cabin_res,
    w_video_hours, w_timelapse_hours,
    w_hours_per_day, w_days_per_week
]
for control in controls: control.observe(calculate_and_update, names='value')
w_print_button.on_click(on_print_button_clicked)

# Display the main container
display(main_container)

# Initial calculation
calculate_and_update({'owner': None})
