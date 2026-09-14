import json
import numpy as np

# coding: utf-8
def get_röster(verbose = 0):
#    n_rödgröna1 = 0
#    n_rödgröna2 = 0
#    n_blågula = 0
#    n_borgerliga = 0
#    n_alla = 0
    n_totalt = 0

    # V, S, MP, C, L, M, KD, SD 
    V = S = MP = C = L = M = KD = SD = 0
    for pr in data['valomrade']['rostfordelning']['rosterPaverkaMandat']['partiRoster']:
        pb = pr['partibeteckning']
        nr = pr['antalRoster']

        n_totalt += nr

        if 'Sociald' in pb:
            S = nr
        if 'Vänster' in pb:
            V = nr
        if 'Miljöpartiet' in pb:
            MP = nr
        if 'Center' in pb:
            C = nr
        if 'Moderat' in pb:
            M = nr
        if 'Liberal' in pb:
            L = nr
        if 'Kristd' in pb:
            KD = nr
        if 'Sveriged' in pb:
            SD = nr
        if verbose:
            print(f"{pb}:\t{nr}")

    # Övriga            
    (pb, n_övriga) = ('Övriga', data['valomrade']['rostfordelning']['rosterPaverkaMandat']['rosterOvrigaPartier']['antalRoster'])
    if verbose:
        print(f"{pb}:\t{n_övriga}")

    # Ogiltiga
    n_totalt += n_övriga
    (pb, n_ogiltiga) = ('Ogiltiga', data['valomrade']['rostfordelning']['rosterEjPaverkaMandat']['antalRoster'])
    if verbose:
        print(f"{pb}:\t{n_ogiltiga}")

    return np.array([V, S, MP, C, L, M, KD, SD, n_övriga, n_ogiltiga, n_totalt, n_totalt + n_ogiltiga])


if __name__ == '__main__':
    with open("valdata_json/Val_2026_preliminar_mandatfordelning_00_RD.json", "r") as f:
        data = json.load(f)

    precision = 1
    [V, S, MP, C, L, M, KD, SD, ÖVR, OG, TOT_G, TOT] = röster = get_röster(0)
    namn = ['V', 'S', 'MP', 'C', 'L', 'M', 'KD', 'SD', 'Övriga', 'Ogiltiga', 'Totalt giltiga', 'Totalt']
    res = dict(zip(namn, röster))
    for key, val in res.items():
        if key in ("Ogiltiga", "Totalt", "Totalt giltiga"):
            continue
        # print(f"{key}:\t\t {(100 * val / TOT_G).round(precision):>6.2f} %")
        print(f"{key}:\t\t {(100 * val / TOT_G):>6.1f} %")
    print()


    RG = V + S + MP + C
    GB = L + M + KD + SD
    RG_PROC = RG / TOT_G
    GB_PROC = GB / TOT_G
    # print(f"{(100 * get_röster()[:9] / TOT_G).round(1)}")
    print(f"Rödgröna:\t{RG:10d}\t\t{( 100 * RG / TOT_G ):>6.2f} %")
    print(f"Gulblåa:\t{GB:10d}\t\t{( 100 * GB / TOT_G ):>6.2f} %")
    print(f"Differens:\t{RG - GB:10d}\t\t{100 * (RG_PROC - GB_PROC):>6.2f} %")
    print(f"Totalt giltiga:\t{TOT_G:10d}")
    print(f"Totalt:\t\t{TOT:10d}")
