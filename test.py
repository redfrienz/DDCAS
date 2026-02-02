import xarray as xr
import pandas as pd
import numpy as np

file_path = './ops_seis-l1b-sgps_g18_d20250101_v0-0-0.nc'

def get_100mev_timeseries_sync(file_path):
    ds = xr.open_dataset(file_path, decode_times=False)
    actual_data_len = ds['T3_DifferentialProtonFluxes'].shape[0]

    time_raw = ds['L1a_SciData_TimeStamp'].values.flatten()
    
    if len(time_raw) > actual_data_len:
        step = len(time_raw) // actual_data_len
        time_raw = time_raw[::step][:actual_data_len]
    
    base_date = pd.Timestamp('2000-01-01 12:00:00')
    timestamps = base_date + pd.to_timedelta(time_raw, unit='s')

    def get_safe_1d(data_array, energy_idx=None):
        temp = data_array
        if energy_idx is not None:
            temp = temp.isel({temp.dims[-1]: energy_idx})

        while len(temp.dims) > 1:
            temp = temp.isel({temp.dims[1]: 0})
            
        return temp.values.flatten()

    # 4. 100MeV 이상 에너지 채널 합산 (P8BF~P10)
    channels = {
        1: 118 - 99,   # P8BF
        2: 150 - 118,  # P8CF
        3: 275 - 150,  # P9F
        4: 500 - 275   # P10
    }

    total_flux = np.zeros(actual_data_len)

    print("🔄 에너지 채널별 적분 계산 중...")
    t3_var = ds['T3_DifferentialProtonFluxes']
    for idx, width in channels.items():
        data_1d = get_safe_1d(t3_var, energy_idx=idx)
        # 1000은 keV^-1 -> MeV^-1 변환용
        total_flux += (data_1d * 1000 * width)

    # 5. P11 Integral Flux (> 500 MeV) 합산
    p11_var = ds['T3P11_IntegralProtonFlux']
    p11_1d = get_safe_1d(p11_var)
    total_flux += p11_1d

    # 6. 결과 DataFrame 생성
    df_final = pd.DataFrame({'Proton_Flux_100MeV': total_flux}, index=timestamps)
    df_final.index.name = 'time'

    print(f"\n✅ 성공! 최종 데이터 형태: {df_final.shape}")
    print(f"🔥 최대 플럭스 값: {df_final['Proton_Flux_100MeV'].max():.4f} pfu")
    
    return df_final

if __name__ == "__main__":
    df_100 = get_100mev_timeseries_sync(file_path)
    print(df_100.head())