import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
from scipy.interpolate import interp1d
from sklearn.linear_model import LinearRegression

plt.rcParams.update({
    'font.size': 14,           # Tamaño de fuente general
    'axes.titlesize': 18,      # Tamaño del título
    'axes.labelsize': 18,      # Tamaño de las etiquetas de los ejes
    'xtick.labelsize': 18,     # Tamaño de los números del eje X
    'ytick.labelsize': 18,     # Tamaño de los números del eje Y
    'legend.fontsize': 18,     # Tamaño de la leyenda
    'figure.titlesize': 18     # Tamaño del título de la figura
})

def get_amplitude_period(red_x, t):
    """
    Versión optimizada de la función original get_amplitude_period
    """
    max_seno = []
    min_seno = []
    max_t = []
    min_t = []

    flag_subiendo = 0
    last_min_max = 0  # 1 si el ultimo ha sido un min, 2 si ha sido un max

    for i in range(1, len(t)-1):
        if (red_x[i] > red_x[i-1] and last_min_max != 2):
            flag_subiendo = 1

        if (red_x[i] < red_x[i-1] and last_min_max != 1):
            flag_subiendo = 0

        if (flag_subiendo == 1 and red_x[i] > red_x[i+1]):
            max_seno.append(red_x[i])
            max_t.append(t[i])
            last_min_max = 2

        if (flag_subiendo == 0 and red_x[i] < red_x[i+1]):
            min_seno.append(red_x[i])
            min_t.append(t[i])
            last_min_max = 1

    if len(min_t) > len(max_t): 
        ts = min_t
    else:
        ts = max_t

    periodo_seno = [ts[i] - ts[i-1] for i in range(1, len(ts))]

    amplitud_seno = []
    if (len(max_seno) >= len(min_seno)):
        for i in range(len(min_seno)):
            amplitud_seno.append(max_seno[i] - min_seno[i])
    else:
        for i in range(len(max_seno)):
            amplitud_seno.append(max_seno[i] - min_seno[i])

    return amplitud_seno, periodo_seno, ts, max_seno, max_t, min_seno, min_t

# ========================
# CARGA Y PROCESAMIENTO DE DATOS
# ========================

# Parámetros
obs_time = 10
video_delay = 0.5  # Delay añadido al video en segundos

# ===== DATOS DE SEÑALES LIVING =====
# filename = "../controlador_robot/data/2021y_12m_1d/15h_33m_8s.txt"
filename = "../data/intervals_data.txt"
dataset = pd.read_csv(filename, delimiter=' ', header=2)
data = dataset.values

start, end = 0, -1
index = [(x / 1000000) - obs_time for x in data[start:end, 0]]  # tiempo en segundos
c = data[start:end, 1]
v_pd = data[start:end, 2]
v_lp = data[start:end, 3]
e_pd = data[start:end, 4]
e_lp = data[start:end, 5]

# DETECCIÓN DE PICOS USANDO EL MÉTODO ORIGINAL (columna 6)
p_raw = data[start:end, 6]
print("=== DETECCIÓN DE PICOS MÉTODO ORIGINAL ===")
print(f"Valores raw período (primeros 10): {p_raw[:10]}")
print(f"Rango: {np.min(p_raw)} - {np.max(p_raw)}")

# Calcular cambios en la columna 6 como en el código original
changes = np.where(np.diff(p_raw) != 0)[0] + 1
period_times = [index[i] for i in changes]
period_first = [p_raw[i] for i in changes]

# Convertir período living a segundos (microsegundos -> segundos)
period_single = [x / 1000 for x in period_first]
period_times_seconds = period_times

print(f"Cambios detectados: {len(changes)}")
print(f"Primeros 10 períodos (s): {period_single[:10]}")
print(f"Rango de períodos: {np.min(period_single):.6f} - {np.max(period_single):.6f} s")

# ===== TAGS CON ÍNDICES DE PEAKS living =====
print("\n=== ÍNDICES DE PEAKS living ===")
for i, (idx, time, period) in enumerate(zip(changes, period_times, period_single)):
    print(f"Peak {i}: índice={idx}, tiempo={time:.3f}s, período={period:.6f}s")

if len(period_times) > 0:
    # Tiempos de los cambios detectados
    period_times_seconds = period_times
    
    # Los períodos ya están calculados arriba como period_single
    print(f"Rango de períodos: {np.min(period_single):.3f} - {np.max(period_single):.3f} s")
else:
    print("ERROR: No se detectaron cambios en la columna 6")
    period_times = []
    period_times_seconds = []
    period_single = []

# Calcular interval_lppd
e_pd_array = np.array(e_pd)
e_lp_array = np.array(e_lp)

lp_indices = np.where(e_lp_array == 1)[0]
pd_indices = np.where(e_pd_array == 1)[0]

interval_lppd = np.zeros(len(index))
if len(lp_indices) > 0 and len(pd_indices) > 0:
    for pd_idx in pd_indices:
        lp_before = lp_indices[lp_indices < pd_idx]
        if len(lp_before) > 0:
            last_lp = lp_before[-1]
            interval_lppd[pd_idx:] = pd_idx - last_lp

interval_lppd = interval_lppd / 10

# Detectar sombras en señales living usando c < -0.5
electrical_shadow_mask = []
for pt in period_times:
    idx = int(np.interp(pt, index, np.arange(len(c))))
    if idx < len(c):
        is_shadow = c[idx] < -0.4
        electrical_shadow_mask.append(is_shadow)
    else:
        electrical_shadow_mask.append(False)

electrical_shadow_mask = np.array(electrical_shadow_mask)

# ===== DATOS DE VIDEO TRACKING =====
filename_video = "../data/legs-tracking.txt"
dataset_video = pd.read_csv(filename_video, delimiter=' ', header=0)
data_video = dataset_video.values

start_video, end_video = 0, -1
t = [(x / 1000) for x in data_video[start_video:end_video, 0]]
red_x = data_video[start_video:end_video, 5]
red_y = data_video[start_video:end_video, 6]

# Normalizar tiempo de video
t = [(x - t[0]) for x in t]

# ===== AÑADIR DELAY AL VIDEO =====
print(f"\n=== AÑADIENDO DELAY DE {video_delay}s AL VIDEO ===")
print(f"Tiempo video antes del delay - Rango: {t[0]:.3f}s a {t[-1]:.3f}s")
t = [(x + video_delay) for x in t]
print(f"Tiempo video después del delay - Rango: {t[0]:.3f}s a {t[-1]:.3f}s")

# ========================
# PROCESAMIENTO DE SEÑAL DE VIDEO
# ========================

N_resampled = 10000
duration = t[-1] - t[0]
sample_rate = N_resampled/duration
f2 = interp1d(t, red_x, kind='cubic')
t_interpl = np.linspace(t[0], t[-1], num=N_resampled, endpoint=True)
red_x_interpl = f2(t_interpl)

ts = t_interpl
red_x = red_x_interpl
t_processed = t_interpl

b, a = signal.butter(3, 2.0, fs=sample_rate)
zi = signal.lfilter_zi(b, a)
z, _ = signal.lfilter(b, a, red_x, zi=zi*red_x[0])
z2, _ = signal.lfilter(b, a, z, zi=zi*z[0])
red_x = signal.filtfilt(b, a, red_x)

b, a = signal.butter(3, 0.45, btype='highpass', fs=sample_rate)
zi = signal.lfilter_zi(b, a)
z, _ = signal.lfilter(b, a, red_x, zi=zi*red_x[0])
z2, _ = signal.lfilter(b, a, z, zi=zi*z[0])
legs_oscillation_display = signal.filtfilt(b, a, red_x)

# Detección de picos y análisis de video
amplitud_seno, periodo_seno, ts, max_seno, max_t, min_seno, min_t = get_amplitude_period(legs_oscillation_display, t_processed)

# ===== TAGS CON ÍNDICES DE PEAKS DE VIDEO =====
print("\n=== ÍNDICES DE PEAKS DE VIDEO (CON DELAY) ===")
for i, (time, amplitude) in enumerate(zip(max_t, max_seno)):
    # Encontrar el índice correspondiente en el array original
    video_idx = np.argmin(np.abs(np.array(t) - time))
    print(f"Peak {i}: índice={video_idx}, tiempo={time:.3f}s, amplitud={amplitude:.3f}")

amplitude_threshold = 17
# Threshold para detección de sombra por amplitud

# Detección de sombra por amplitud
tags = []
for amp in amplitud_seno:
    is_shadow = amp > amplitude_threshold
    tags.append(is_shadow)

print(f"\nDetección de sombra por amplitud:")
print(f"Total de picos: {len(amplitud_seno)}")
print(f"Picos en sombra (amplitud > {amplitude_threshold}): {np.sum(tags)}")

# ===== TAGS DE SOMBRA CON ÍNDICES =====
print("\n=== TAGS DE SOMBRA (VIDEO CON DELAY) ===")
for i, (amp, is_shadow) in enumerate(zip(amplitud_seno, tags)):
    status = "SOMBRA" if is_shadow else "LUZ"
    print(f"Peak {i}: amplitud={amp:.3f}, estado={status}")

# Normalizar amplitudes
if amplitud_seno:
    amplitud_seno_norm = np.array(amplitud_seno) / np.max(amplitud_seno)
else:
    amplitud_seno_norm = []


# ========================
# SINCRONIZACIÓN DE DATOS
# ========================

def find_shadow_transitions(shadow_mask):
    transitions = []
    for i in range(1, len(shadow_mask)):
        if not shadow_mask[i-1] and shadow_mask[i]:
            transitions.append(('enter', i))
        elif shadow_mask[i-1] and not shadow_mask[i]:
            transitions.append(('exit', i))
    return transitions

electrical_transitions = find_shadow_transitions(electrical_shadow_mask)
video_transitions = find_shadow_transitions(tags)

print(f"\nElectrical shadow transitions: {electrical_transitions}")
print(f"Video shadow transitions: {video_transitions}")

# ========================
# PLOT ADICIONAL: v_lp ANTES DEL REAJUSTE DE TIEMPO
# ========================
print("\n=== CREANDO PLOT v_lp ANTES DEL REAJUSTE ===")

plt.figure(figsize=(15, 6))

# Mostrar toda la señal v_lp con tiempo original
plt.plot(index, v_lp, 'steelblue', alpha=0.7, linewidth=1, label='v_lp signal')

# Marcar todos los picos living con tiempo original (SIN TAGS)
v_lp_interp = np.interp(period_times, index, v_lp)
for i, (time, value) in enumerate(zip(period_times, v_lp_interp)):
    if i < len(electrical_shadow_mask):
        color = 'red' if electrical_shadow_mask[i] else 'blue'
        size = 80 if electrical_shadow_mask[i] else 50
        plt.scatter(time, value, c=color, s=size, alpha=0.8, 
                   edgecolors='black', linewidth=1, zorder=5)

plt.xlabel('Time (s) - Original')
plt.ylabel('v_lp (mV)')
plt.title('v_lp Signal BEFORE Time Reset - All Peaks')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('plot_vlp_before_time_reset.png', dpi=300, bbox_inches='tight')
plt.show()

# Sincronización basada en sombras
if len(electrical_transitions) >= 2 and len(video_transitions) >= 2:
    elec_first_shadow = next((idx for action, idx in electrical_transitions if action == 'enter'), 0)
    video_first_shadow = next((idx for action, idx in video_transitions if action == 'enter'), 0)
    
    elec_second_exit = None
    video_second_exit = None
    
    shadow_count = 0
    for action, idx in electrical_transitions:
        if action == 'exit':
            shadow_count += 1
            if shadow_count == 2:
                elec_second_exit = idx
                break
    
    shadow_count = 0
    for action, idx in video_transitions:
        if action == 'exit':
            shadow_count += 1
            if shadow_count == 2:
                video_second_exit = idx
                break
    
    if elec_second_exit is not None and video_second_exit is not None:
        video_before_first = video_first_shadow
        video_after_second = len(tags) - video_second_exit
        
        elec_start = max(0, elec_first_shadow - video_before_first)
        elec_end = min(len(period_times), elec_second_exit + video_after_second)
        
        # Recortar arrays living
        period_times_sync = period_times[elec_start:elec_end]
        period_times_seconds_sync = period_times_seconds[elec_start:elec_end]
        period_single_sync = period_single[elec_start:elec_end]
        electrical_shadow_mask_sync = electrical_shadow_mask[elec_start:elec_end]
        
        # RESETEAR TIEMPO living al primer peak azul
        first_blue_peak_idx = None
        for i, is_shadow in enumerate(electrical_shadow_mask_sync):
            if not is_shadow:
                first_blue_peak_idx = i
                break
        
        if first_blue_peak_idx is not None:
            time_offset = period_times_seconds_sync[first_blue_peak_idx]
            print(f"Reseteando tiempo: primer peak azul en {time_offset:.3f}s → 0s")
            
            period_times_sync = [t - time_offset for t in period_times_sync]
            period_times_seconds_sync = [t - time_offset for t in period_times_seconds_sync]
        else:
            time_offset = 0
        
        # Muestrear interval_lppd para puntos sincronizados
        interval_sampled_sync = []
        for pt in period_times_sync:
            pt_original = pt + time_offset
            idx = int(np.interp(pt_original, index, np.arange(len(interval_lppd))))
            if idx < len(interval_lppd):
                interval_sampled_sync.append(interval_lppd[idx])
        
        # Normalizar DESPUÉS del muestreo
        if len(interval_sampled_sync) > 0:
            interval_sampled_sync = np.array(interval_sampled_sync) / np.max(interval_sampled_sync)
        
        print(f"Synchronized lengths:")
        print(f"  Electrical periods: {len(period_single_sync)}")
        print(f"  Video periods: {len(periodo_seno)}")
        
    else:
        # Sin sincronización
        period_times_sync = period_times
        period_times_seconds_sync = period_times_seconds
        period_single_sync = period_single
        electrical_shadow_mask_sync = electrical_shadow_mask
        time_offset = 0
        
        interval_sampled_sync = []
        for pt in period_times_sync:
            idx = int(np.interp(pt, index, np.arange(len(interval_lppd))))
            if idx < len(interval_lppd):
                interval_sampled_sync.append(interval_lppd[idx])
        
        if len(interval_sampled_sync) > 0:
            interval_sampled_sync = np.array(interval_sampled_sync) / np.max(interval_sampled_sync)
            
else:
    # Sin suficientes transiciones
    period_times_sync = period_times
    period_times_seconds_sync = period_times_seconds
    period_single_sync = period_single
    electrical_shadow_mask_sync = electrical_shadow_mask
    time_offset = 0
    
    interval_sampled_sync = []
    for pt in period_times_sync:
        idx = int(np.interp(pt, index, np.arange(len(interval_lppd))))
        if idx < len(interval_lppd):
            interval_sampled_sync.append(interval_lppd[idx])
    
    if len(interval_sampled_sync) > 0:
        interval_sampled_sync = np.array(interval_sampled_sync) / np.max(interval_sampled_sync)

# ========================
# ELIMINACIÓN DEL PRIMER Y ÚLTIMO PEAK
# ========================

# ELIMINAR PRIMER Y ÚLTIMO PEAK living
if len(period_times_sync) > 2:
    print(f"\nEliminando primer peak living en tiempo: {period_times_seconds_sync[0]:.3f}s")
    #print(f"Eliminando último peak living en tiempo: {period_times_seconds_sync[-1]:.3f}s")
    
    # Remover el primer y último elemento de todos los arrays living sincronizados
    period_times_sync = period_times_sync[1:]
    period_times_seconds_sync = period_times_seconds_sync[1:]
    period_single_sync = period_single_sync[1:]
    electrical_shadow_mask_sync = electrical_shadow_mask_sync[1:]
    
    # Recalcular interval_sampled_sync sin el primer y último peak
    interval_sampled_sync = []
    for pt in period_times_sync:
        pt_original = pt + time_offset
        idx = int(np.interp(pt_original, index, np.arange(len(interval_lppd))))
        if idx < len(interval_lppd):
            interval_sampled_sync.append(interval_lppd[idx])
    
    # Normalizar DESPUÉS del muestreo
    if len(interval_sampled_sync) > 0:
        interval_sampled_sync = np.array(interval_sampled_sync) / np.max(interval_sampled_sync)
    
    print(f"Peaks living restantes: {len(period_single_sync)}")
elif len(period_times_sync) > 1:
    print(f"\nSolo eliminando primer peak living (no hay suficientes peaks para eliminar el último)")
    # Código original para solo primer peak
    period_times_sync = period_times_sync[1:]
    period_times_seconds_sync = period_times_seconds_sync[1:]
    period_single_sync = period_single_sync[1:]
    electrical_shadow_mask_sync = electrical_shadow_mask_sync[1:]
    
    interval_sampled_sync = []
    for pt in period_times_sync:
        pt_original = pt + time_offset
        idx = int(np.interp(pt_original, index, np.arange(len(interval_lppd))))
        if idx < len(interval_lppd):
            interval_sampled_sync.append(interval_lppd[idx])
    
    if len(interval_sampled_sync) > 0:
        interval_sampled_sync = np.array(interval_sampled_sync) / np.max(interval_sampled_sync)
    
    print(f"Peaks living restantes: {len(period_single_sync)}")

# ELIMINAR PRIMER Y ÚLTIMO PEAK DE VIDEO
if len(amplitud_seno) > 2 and len(periodo_seno) > 2:
    print(f"Eliminando primer peak de video en tiempo: {ts[1]:.3f}s")
    #print(f"Eliminando último peak de video en tiempo: {ts[-1]:.3f}s")
    
    # Remover el primer y último elemento de todos los arrays de video
    amplitud_seno = amplitud_seno[1:]
    periodo_seno = periodo_seno[1:]
    ts = ts[2:-1]  # Ajustar ts apropiadamente
    max_seno = max_seno[1:] if len(max_seno) > 2 else max_seno
    max_t = max_t[1:] if len(max_t) > 2 else max_t
    min_seno = min_seno[1:] if len(min_seno) > 2 else min_seno
    min_t = min_t[1:] if len(min_t) > 2 else min_t
    tags = tags[1:] if len(tags) > 2 else tags
    
    # Recalcular amplitudes normalizadas
    if amplitud_seno:
        amplitud_seno_norm = np.array(amplitud_seno) / np.max(amplitud_seno)
    else:
        amplitud_seno_norm = []
    
    print(f"Peaks de video restantes: {len(amplitud_seno)}")
elif len(amplitud_seno) > 1 and len(periodo_seno) > 1:
    print(f"Solo eliminando primer peak de video (no hay suficientes peaks para eliminar el último)")
    # Código original para solo primer peak
    amplitud_seno = amplitud_seno[1:]
    periodo_seno = periodo_seno[1:]
    ts = ts[2:]
    max_seno = max_seno[1:] if len(max_seno) > 1 else max_seno
    max_t = max_t[1:] if len(max_t) > 1 else max_t
    min_seno = min_seno[1:] if len(min_seno) > 1 else min_seno
    min_t = min_t[1:] if len(min_t) > 1 else min_t
    tags = tags[1:] if len(tags) > 1 else tags
    
    if amplitud_seno:
        amplitud_seno_norm = np.array(amplitud_seno) / np.max(amplitud_seno)
    else:
        amplitud_seno_norm = []
    
    print(f"Peaks de video restantes: {len(amplitud_seno)}")

# ========================
# VISUALIZACIÓN MEJORADA (SIN PRIMEROS PEAKS) SIN TAGS
# ========================

# ========================
# CALCULAR RANGOS COMUNES PARA PLOTS 1 Y 2
# ========================

# Calcular rangos para ejes X (períodos)
x_data_plot1 = period_single_sync if len(period_single_sync) > 0 else []
x_data_plot2 = periodo_seno if len(periodo_seno) > 0 else []

if len(x_data_plot1) > 0 and len(x_data_plot2) > 0:
    x_min_common = min(np.min(x_data_plot1), np.min(x_data_plot2))
    x_max_common = max(np.max(x_data_plot1), np.max(x_data_plot2))
    x_range_common = x_max_common - x_min_common
    x_margin = x_range_common * 0.05  # 5% de margen
    x_lim_common = [x_min_common - x_margin, x_max_common + x_margin]
else:
    x_lim_common = None

# Calcular rangos para ejes Y
y_data_plot1 = interval_sampled_sync if len(interval_sampled_sync) > 0 else []
y_data_plot2 = amplitud_seno_norm if len(amplitud_seno_norm) > 0 else []

if len(y_data_plot1) > 0 and len(y_data_plot2) > 0:
    y_min_common = min(np.min(y_data_plot1), np.min(y_data_plot2))
    y_max_common = max(np.max(y_data_plot1), np.max(y_data_plot2))
    y_range_common = y_max_common - y_min_common
    y_margin = y_range_common * 0.05  # 5% de margen
    y_lim_common = [y_min_common - y_margin, y_max_common + y_margin]
else:
    y_lim_common = None

# Calcular rangos para colorbar (tiempo)
time_data_plot1 = period_times_seconds_sync if len(period_times_seconds_sync) > 0 else []
time_data_plot2 = ts if len(ts) > 0 else []

if len(time_data_plot1) > 0 and len(time_data_plot2) > 0:
    time_min_common = min(np.min(time_data_plot1), np.min(time_data_plot2))
    time_max_common = max(np.max(time_data_plot1), np.max(time_data_plot2))
    colorbar_lim_common = [time_min_common, time_max_common]
else:
    colorbar_lim_common = None

print(f"\n=== RANGOS COMUNES CALCULADOS ===")
if x_lim_common:
    print(f"Eje X (períodos): {x_lim_common[0]:.3f} - {x_lim_common[1]:.3f}")
if y_lim_common:
    print(f"Eje Y (amplitud/interval): {y_lim_common[0]:.3f} - {y_lim_common[1]:.3f}")
if colorbar_lim_common:
    print(f"Colorbar (tiempo): {colorbar_lim_common[0]:.3f} - {colorbar_lim_common[1]:.3f}")

# Plot 1: interval_lppd vs period (sin primer peak living) SIN TAGS
plt.figure(figsize=(12, 8))
if len(period_single_sync) > 0 and len(interval_sampled_sync) > 0:
    min_len = min(len(period_single_sync), len(interval_sampled_sync), len(electrical_shadow_mask_sync))
    if min_len > 0:
        
        shadow_indices = electrical_shadow_mask_sync[:min_len]
        light_indices = ~shadow_indices  # Puntos NO en sombra
        
        # Puntos en sombra (rojos)
        if np.any(shadow_indices):
            shadow_periods = np.array(period_single_sync[:min_len])[shadow_indices]
            shadow_intervals = np.array(interval_sampled_sync[:min_len])[shadow_indices]
            plt.scatter(shadow_periods, shadow_intervals, 
                       color='red', s=180, alpha=0.6, label='Shadow')
        
        # Puntos en luz (azules)
        if np.any(light_indices):
            light_periods = np.array(period_single_sync[:min_len])[light_indices]
            light_intervals = np.array(interval_sampled_sync[:min_len])[light_indices]
            plt.scatter(light_periods, light_intervals, 
                       color='blue', s=180, alpha=0.6, label='Light')
        
        # Scatter plot con colorbar (todos los puntos) SIN TAGS
        scatter = plt.scatter(period_single_sync[:min_len], 
                             interval_sampled_sync[:min_len],
                             c=period_times_seconds_sync[:min_len], 
                             cmap='Blues', s=100,
                             vmin=colorbar_lim_common[0] if colorbar_lim_common else None,
                             vmax=colorbar_lim_common[1] if colorbar_lim_common else None)
        
        # Regresión lineal de todos los puntos
        if min_len > 1:  # Necesitamos al menos 2 puntos para regresión
            X = np.array(period_single_sync[:min_len]).reshape(-1, 1)
            y = np.array(interval_sampled_sync[:min_len])
            
            reg = LinearRegression().fit(X, y)
            x_range = np.linspace(np.min(period_single_sync[:min_len]), 
                                 np.max(period_single_sync[:min_len]), 100)
            y_pred = reg.predict(x_range.reshape(-1, 1))
            
            r2_score = reg.score(X, y)
            plt.plot(x_range, y_pred, 'steelblue', linewidth=1, linestyle='-', 
                    label=f'R²={r2_score:.2f}')
        else:
            reg = None
            print("Warning: No hay suficientes puntos para regresión lineal en Plot 1")
        
        plt.legend()
        plt.colorbar(scatter, label='Time (s)')

# Aplicar rangos comunes
if x_lim_common:
    plt.xlim(x_lim_common)
if y_lim_common:
    plt.ylim(y_lim_common)

plt.xlabel('LP Period (s)')
plt.ylabel('LPPD interval (normalized) (s)')
plt.title(f'Interval LP-PD vs Period')
#plt.grid(True, alpha=0.3)
#plt.tick_params(axis='both', which='major', labelsize=12)
plt.tight_layout()
plt.savefig(f'plot1_interval_vs_period.svg', bbox_inches='tight')
plt.show()

# Plot 2: Período vs Amplitud de las patas (sin primer peak de video) SIN TAGS
plt.figure(figsize=(12, 8))
if len(periodo_seno) > 0 and len(amplitud_seno_norm) > 0:
    min_len_video = min(len(periodo_seno), len(amplitud_seno_norm), len(ts))
    
    tags_array = np.array(tags[:min_len_video])
    light_tags = ~tags_array  # Puntos NO en sombra
    
    # Puntos en sombra (rojos)
    if len(tags_array) > 0 and np.any(tags_array):
        shadow_periods = np.array(periodo_seno[:min_len_video])[tags_array]
        shadow_amplitudes = np.array(amplitud_seno_norm[:min_len_video])[tags_array]
        plt.scatter(shadow_periods, shadow_amplitudes, 
                   color='red', s=180, alpha=0.6, label='Shadow')
    
    # Puntos en luz (azules)
    if len(tags_array) > 0 and np.any(light_tags):
        light_periods = np.array(periodo_seno[:min_len_video])[light_tags]
        light_amplitudes = np.array(amplitud_seno_norm[:min_len_video])[light_tags]
        plt.scatter(light_periods, light_amplitudes, 
                   color='blue', s=180, alpha=0.6, label='Light')
    
    # Scatter plot con colorbar (todos los puntos) SIN TAGS
    scatter = plt.scatter(periodo_seno[:min_len_video], 
                         amplitud_seno_norm[:min_len_video],
                         c=ts[:min_len_video], 
                         cmap='Blues', s=100,
                         vmin=colorbar_lim_common[0] if colorbar_lim_common else None,
                         vmax=colorbar_lim_common[1] if colorbar_lim_common else None)
    
    # Regresión lineal de todos los puntos
    if min_len_video > 1:  # Necesitamos al menos 2 puntos para regresión
        X_video = np.array(periodo_seno[:min_len_video]).reshape(-1, 1)
        y_video = np.array(amplitud_seno_norm[:min_len_video])
        
        reg_video = LinearRegression().fit(X_video, y_video)
        x_range_video = np.linspace(np.min(periodo_seno[:min_len_video]), 
                                   np.max(periodo_seno[:min_len_video]), 100)
        y_pred_video = reg_video.predict(x_range_video.reshape(-1, 1))
        
        r2_score_video = reg_video.score(X_video, y_video)
        plt.plot(x_range_video, y_pred_video, 'steelblue', linewidth=1, linestyle='-', 
                label=f'R²={r2_score_video:.2f}')
    else:
        reg_video = None
        print("Warning: No hay suficientes puntos para regresión lineal en Plot 2")
    
    plt.legend()
    plt.colorbar(scatter, label='Time (s)')

# Aplicar rangos comunes
if x_lim_common:
    plt.xlim(x_lim_common)
if y_lim_common:
    plt.ylim(y_lim_common)

plt.xlabel('Legs Period (s)')
plt.ylabel('Legs amplitude (normalized) (cm)')
plt.title(f'Legs Period vs Amplitude')
#plt.grid(True, alpha=0.3)
#plt.tick_params(axis='both', which='major', labelsize=14)
plt.tight_layout()
plt.savefig(f'plot2_legs_period_vs_amplitude.svg', bbox_inches='tight')
plt.show()

# Plot 3: Señales sincronizadas (actualizado para reflejar cambios) SIN TAGS
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

# Subplot 1: v_lp con tiempo reseteado (sin primer peak) SIN TAGS
if len(period_times_sync) > 0:
    electrical_start_original = period_times_sync[0] + time_offset
    electrical_end_original = period_times_sync[-1] + time_offset
    
    mask_range = (np.array(index) >= electrical_start_original) & (np.array(index) <= electrical_end_original)
    index_filtered = np.array(index)[mask_range]
    v_lp_filtered = np.array(v_lp)[mask_range]
    
    # Restar offset al tiempo para mostrar
    index_filtered_reset = index_filtered - time_offset
    
    ax1.plot(index_filtered_reset, v_lp_filtered, 'steelblue', alpha=0.7, linewidth=1)
    
    # Marcar picos con tiempo reseteado (sin primer peak) SIN TAGS
    v_lp_interp = np.interp([t + time_offset for t in period_times_sync], index, v_lp)
    for i, (time, value) in enumerate(zip(period_times_sync, v_lp_interp)):
        if i < len(electrical_shadow_mask_sync):
            color = 'red' if electrical_shadow_mask_sync[i] else 'blue'
            size = 80 if electrical_shadow_mask_sync[i] else 50
            ax1.scatter(time, value, c=color, s=size, alpha=0.8, 
                       edgecolors='black', linewidth=1, zorder=5)
    
    ax1.set_xlim(period_times_sync[0], period_times_sync[-1])

ax1.set_ylabel('v_lp (mV)')
ax1.set_title(f'v_lp Signal')
ax1.grid(True, alpha=0.3)

# Subplot 2: Señal de patas (sin primer peak) SIN TAGS
time_start = period_times_sync[0] if len(period_times_sync) > 0 else 0
time_end = period_times_sync[-1] if len(period_times_sync) > 0 else max(t)

mask_range_video = (np.array(t_processed) >= time_start) & (np.array(t_processed) <= time_end)
t_filtered = np.array(t_processed)[mask_range_video]
legs_filtered = np.array(legs_oscillation_display)[mask_range_video]

ax2.plot(t_filtered, legs_filtered, 'red', alpha=0.7, linewidth=1)

# Marcar picos del video (sin primer peak) SIN TAGS
if len(max_t) > 0:
    for i, (time, value) in enumerate(zip(max_t, max_seno)):
        if i < len(tags):
            color = 'red' if tags[i] else 'blue'
            size = 100 if tags[i] else 50
            ax2.scatter(time, value, c=color, s=size, alpha=0.8, 
                       edgecolors='black', linewidth=1, zorder=5)

ax2.set_xlim(time_start, time_end)
ax2.set_ylabel('Legs Position')
ax2.set_xlabel('Time (s)')
ax2.set_title(f'Legs Oscillation')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'plot3_synchronized_signals.png', dpi=300, bbox_inches='tight')
plt.show()

# ========================
# ESTADÍSTICAS FINALES (ACTUALIZADAS)
# ========================

print(f"\n=== ESTADÍSTICAS FINALES (CON DELAY DE {video_delay}s EN VIDEO) ===")
print(f"Peaks living restantes: {len(period_single_sync)}")
if len(period_single_sync) > 0:
    print(f"Período living promedio: {np.mean(period_single_sync):.3f} ± {np.std(period_single_sync):.3f} s")

print(f"Peaks de video restantes: {len(max_seno)}")
print(f"Picos de video en sombra: {np.sum(tags)}")
if len(periodo_seno) > 0:
    print(f"Período video promedio: {np.mean(periodo_seno):.3f} ± {np.std(periodo_seno):.3f} s")

if len(period_single_sync) > 0 and len(periodo_seno) > 0:
    ratio = np.mean(period_single_sync) / np.mean(periodo_seno)
    print(f"Ratio período living/video: {ratio:.2f}")

print(f"\n=== INFORMACIÓN DE REGRESIÓN (CON DELAY DE {video_delay}s) ===")
if 'reg' in locals() and reg is not None:
    print(f"Plot 1 - Coeficiente de regresión: {reg.coef_[0]:.6f}")
    print(f"Plot 1 - Intercepto: {reg.intercept_:.6f}")
    print(f"Plot 1 - R²: {r2_score:.6f}")
else:
    print("Plot 1 - No se pudo calcular regresión (datos insuficientes)")

if 'reg_video' in locals() and reg_video is not None:
    print(f"Plot 2 - Coeficiente de regresión: {reg_video.coef_[0]:.6f}")
    print(f"Plot 2 - Intercepto: {reg_video.intercept_:.6f}")
    print(f"Plot 2 - R²: {r2_score_video:.6f}")
else:
    print("Plot 2 - No se pudo calcular regresión (datos insuficientes)")

# ========================
# ANÁLISIS DE CORRESPONDENCIA DE ÍNDICES
# ========================

print(f"\n=== ANÁLISIS DE CORRESPONDENCIA DE ÍNDICES (CON DELAY {video_delay}s) ===")
print("Verificando si los índices tienen sentido cronológicamente...")

# Verificar orden cronológico de peaks living
print("\nPeaks living (después de eliminación):")
for i, (time, period, is_shadow) in enumerate(zip(period_times_seconds_sync, period_single_sync, electrical_shadow_mask_sync)):
    status = "SOMBRA" if is_shadow else "LUZ"
    print(f"  Índice {i}: tiempo={time:.3f}s, período={period:.6f}s, estado={status}")

# Verificar orden cronológico de peaks de video
print(f"\nPeaks de video (después de eliminación, CON DELAY {video_delay}s):")
for i, (time, amp, is_shadow) in enumerate(zip(max_t, amplitud_seno, tags)):
    status = "SOMBRA" if is_shadow else "LUZ"
    print(f"  Índice {i}: tiempo={time:.3f}s, amplitud={amp:.3f}, estado={status}")

# Verificar sincronización
print(f"\n=== VERIFICACIÓN DE SINCRONIZACIÓN (CON DELAY {video_delay}s) ===")
if len(period_times_seconds_sync) > 0 and len(max_t) > 0:
    elec_duration = period_times_seconds_sync[-1] - period_times_seconds_sync[0]
    video_duration = max_t[-1] - max_t[0]
    print(f"Duración ventana eléctrica: {elec_duration:.3f}s")
    print(f"Duración ventana video (con delay): {video_duration:.3f}s")
    print(f"Diferencia de duración: {abs(elec_duration - video_duration):.3f}s")
    
    # Comparar estados de sombra
    min_len_comparison = min(len(electrical_shadow_mask_sync), len(tags))
    if min_len_comparison > 0:
        matches = 0
        for i in range(min_len_comparison):
            elec_shadow = electrical_shadow_mask_sync[i]
            video_shadow = tags[i]
            match = elec_shadow == video_shadow
            if match:
                matches += 1
            print(f"  Índice {i}: living={'SOMBRA' if elec_shadow else 'LUZ'}, "
                  f"Video={'SOMBRA' if video_shadow else 'LUZ'}, "
                  f"Match={'✓' if match else '✗'}")
        
        match_percentage = (matches / min_len_comparison) * 100
        print(f"\nCoincidencia de estados: {matches}/{min_len_comparison} ({match_percentage:.1f}%)")
    
print(f"\n=== ANÁLISIS COMPLETADO (CON DELAY {video_delay}s) ===")
print("Revisa los plots generados para verificar visualmente la correspondencia.")