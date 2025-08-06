import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np
# import pingouin as pg


fig_width =  12
start_video = 0
end_video = -1
cm_per_px = 0.03

intervals_tags = ["lppd", "pd"]

experiments = ["experiment1", "experiment2", "experiment3", "experiment4", "experiment5"]
n_exp = len(experiments)

times = []
x_coords = []
curves = []
smooth = []
times_smooth = []
distances = []
aux = []
aux_2 = []
n = 25 * 1 # 25 ptos son un 1s
#n = 25 // 2 # 25 ptos son un 1s

for i in range(n_exp):
    times.append({})
    times_dict = times[-1]

    x_coords.append({})
    x_coords_dict = x_coords[-1]

    curves.append({})
    curves_dict = curves[-1]

    smooth.append({})
    smooth_dict = smooth[-1]

    times_smooth.append({})
    times_smooth_dict = times_smooth[-1]

    distances.append({})
    distances_dict = distances[-1]

    aux.append({})
    aux_dict = aux[-1]

    aux_2.append({})
    aux_dict_2 = aux_2[-1]

    for tag in intervals_tags:
        tracking_file = "captura_patas_videos/"+experiments[i]+"_"+tag+".txt"

        data_video = pd.read_csv(tracking_file, delimiter=" ").values
        times_dict[tag] = [x/1000 for x in data_video[start_video:end_video, 0]] # time in s
        x_coords_dict[tag] = data_video[start_video:end_video, 3]

        distances_dict[tag] = []
        aux_dict[tag] = []
        aux_dict_2[tag] = []
        smooth_dict[tag] = []
        times_smooth_dict[tag] = []

        for k in range(n, len(times_dict[tag][n:]), n):
            smooth_dict[tag].append(np.mean(x_coords_dict[tag][k-n:k]))
            times_smooth_dict[tag].append((times_dict[tag][k] + times_dict[tag][k-n]) / 2)

        distances_dict[tag] = np.absolute(np.gradient(smooth_dict[tag])) * cm_per_px


ini = 0


from scipy.stats import ttest_ind, ttest_rel, f_oneway, mannwhitneyu

# H0: LPPD interval and PD burst distances are equal

for i in range(len(distances)):
    print(distances[i]['lppd'].shape, distances[i]['pd'].shape)

def test(test,equal_var=True, verbose=True, center='median'):
    p_values = []
    for i in range(n_exp):
        # if i == 3:
        #     ini = 10
        # else:
        #     ini = 0

        d_lppd = list(distances[i]['lppd'][ini:])
        d_pd = list(distances[i]['pd'][ini:])

        # Realiza la prueba t de Student
        if not equal_var:
            t_stat, p_value = test(d_lppd, d_pd, equal_var=equal_var)
        else:
            t_stat, p_value = test(d_lppd, d_pd)

        if test == stats.levene:
            t_stat, p_value = test(d_lppd, d_pd, center=center)


        if verbose:
            # Imprime los resultados
            print(f"Experiment {i+1}:")
            # print(f"T-statistic: {t_stat}")
            print(f"P-value: {p_value}")

            # Determina si la diferencia es significativa (usando un valor alfa típico de 0.05)
            if p_value < 0.05:
                print("\tDiferencia significativa")
            else:
                print("\tNo hay diferencia significativa")
        else:
            p_values.append(p_value)

    print(str(p_values).replace(',',';').replace('.',','))

print("\n\nt-test")
test(stats.ttest_ind)
print("\n\nt-test Welsch")
test(stats.ttest_ind, False)
print("\n\nmannwhitneyu")
test(stats.mannwhitneyu)

#    Prueba de Kolmogorov-Smirnov:
#   Se utiliza para comparar dos distribuciones para determinar si provienen
#   de la misma población. Es adecuada si quieres comparar la forma de las distribuciones
#   en lugar de medias o medianas.
print("\n\nKolmogorov-Smirnov")
test(stats.ks_2samp)

"""
    F-test
        Esta prueba se utiliza para determinar si las diferencias en las varianzas entre dos grupos
        son estadísticamente significativas.
"""
print("\n\nf-test")
test(stats.f_oneway)



print("\n\nt-test")
test(stats.ttest_ind, verbose=False)
print("\n\nt-test Welsch")
test(stats.ttest_ind, False, verbose=False)
print("\n\nmannwhitneyu")
test(stats.mannwhitneyu, verbose=False)

#    Prueba de Kolmogorov-Smirnov:
#   Se utiliza para comparar dos distribuciones para determinar si provienen
#   de la misma población. Es adecuada si quieres comparar la forma de las distribuciones
#   en lugar de medias o medianas.
print("\n\nKolmogorov-Smirnov")
test(stats.ks_2samp, verbose=False)

"""
    F-test
        Esta prueba se utiliza para determinar si las diferencias en las varianzas entre dos grupos
        son estadísticamente significativas.
"""
print("\n\nf-test")
test(stats.f_oneway, verbose=False)


"""
    Test de Levene. 
    El Test de Levene evalúa la hipótesis nula de que las varianzas de los diferentes grupos son iguales.
    Si el valor p del test es significativo, podrías concluir que hay evidencia suficiente para rechazar
    la hipótesis nula, lo que indica que las varianzas son diferentes entre los grupos.
"""

print("\n\nTest Levene")
# https://www.statology.org/levenes-test-python/
# ‘trimmed’: recommended for heavy-tailed distributions.
test(stats.levene, verbose=False, center='mean')
print("\n\nTest Levene median")
test(stats.levene, verbose=False, center='median')
print("\n\nTest Levene trimmed")
test(stats.levene, verbose=False, center='trimmed')

"""
 test de Bartlett. El test de Bartlett también evalúa la homogeneidad de varianzas, pero asume que los datos siguen una distribución normal.
"""
print("\n\nTest bartlett")

test(stats.bartlett, verbose=False)



fig, axs = plt.subplots(1, n_exp, figsize=(fig_width, 4), sharey=True)

for i in range(n_exp):
    data_for_boxplot = [distances[i]["lppd"][ini:], distances[i]["pd"][ini:]]

    bplot = axs[i].boxplot(data_for_boxplot, notch=True, widths=0.6, patch_artist=True)
    axs[i].set_title('Experiment %d'%(i+1))
    axs[i].set_xticks(np.arange(1, 3))
    axs[i].set_xticklabels(["LPPD", "PD"])

    # fill with colors
    colors = ['lightsteelblue', 'moccasin']
    colors = ['blue', 'orange']
    for patch, color in zip(bplot['boxes'], colors):
        patch.set_facecolor(color)

axs[0].set_ylabel("Speed (cm/s)")
plt.tight_layout()
plt.show()

meanslp = []
meanspd = []
stdslp = []
stdspd = []

for i in range(n_exp):
        d_lppd = list(distances[i]['lppd'][ini:])
        d_pd = list(distances[i]['pd'][ini:])


        meanslp = np.append(meanslp, np.mean(d_lppd))
        meanspd = np.append(meanspd, np.mean(d_pd))
        stdslp = np.append(stdslp, np.std(d_lppd))
        stdspd = np.append(stdspd, np.std(d_pd))

plt.xlabel("Experiment No.")
plt.ylabel("Standard Deviation")
plt.title("With all timesteps n = 25*2")

plt.bar([1,2,3,4,5], stdslp, width=0.2, label='LPPD interval', color=colors[0])
plt.bar([1.3,2.3,3.3,4.3,5.3], stdspd, width=0.2, label='PD burst', color=colors[1])


plt.legend()
plt.show()
