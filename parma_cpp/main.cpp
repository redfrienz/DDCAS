#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstdlib>

using namespace std;

double getHPcpp(int iy0, int im0, int id0);
double getrcpp(double cido, double ckei);
double getdcpp(double alti, double cido);
double getSpecCpp(int ip, double s, double r, double d, double e, double g);
double get511fluxCpp(double s, double r, double d);

double calculate_sep_spectrum(double flux_100, double energy_mev, double d_depth) {
    if (energy_mev < 100.0) return 0.0;

    double gamma = 1.8; 

    double C = flux_100 * (gamma - 1.0) * pow(50, gamma - 1.0);

    double flux_top = C * pow(energy_mev, -gamma);

    double lambda = 50;
    double attenuation = exp(-d_depth / lambda);

    return flux_top * attenuation;
}
;

int main(int argc, char* argv[]) {

    const int nebin = 140; 
    const int npart = 33;  
    
    double emid[nebin + 2], ewid[nebin + 2];
    double dcc[npart + 1][nebin + 1] = {}; 

    // 기본 입력값
    int year = 2025, month = 1, day = 1;
    double lat = 37.5, lon = 127.0;
    double alt_ft = 35000.0;
    double g_param = -1.5;
    double goes_proton_flux = 0.0;

    if (argc >= 8) {
        year = atoi(argv[1]);
        month = atoi(argv[2]);
        day = atoi(argv[3]);
        lat = atof(argv[4]);
        lon = atof(argv[5]);
        alt_ft = atof(argv[6]);
        g_param = atof(argv[7]);
    }

    if (argc >= 9) {
        goes_proton_flux = atof(argv[8]) / 86400; 
    }

    string dcc_path = "dcc/ICRP116.inp";
    ifstream dccf(dcc_path.c_str(), ios::in);
    if (!dccf.is_open()) { return 1; }
    string str;
    getline(dccf, str); getline(dccf, str);
    for(int ie = 1; ie <= nebin; ie++) {
        getline(dccf, str);
        istringstream dccf1(str);
        dccf1 >> emid[ie] >> ewid[ie];
        for(int ip = 0; ip <= npart; ip++) { dccf1 >> dcc[ip][ie]; }
    }
    dccf.close();

    double s = getHPcpp(year, month, day); 
    double r = getrcpp(lat, lon);      
    double alt_km = alt_ft * 0.3048 * 0.001; 
    double d = getdcpp(alt_km, lat);      

    double gcr_dose_pSv_s = 0.0; 


    for(int ie = 1; ie <= nebin; ie++) {
        double e = emid[ie];

        double sep_proton_flux_at_e = calculate_sep_spectrum(goes_proton_flux, e, d);

        for(int ip = 0; ip <= npart; ip++) {
            double flux = getSpecCpp(ip, s, r, d, e, g_param);

            if(ip == 33 && ie == 78) flux += get511fluxCpp(s, r, d) / ewid[ie];

            double flux_sep = 0.0;
            if (ip == 2 && r < 0.4445) { 
                flux_sep = sep_proton_flux_at_e;
            }

            double total_flux = flux + flux_sep;
            gcr_dose_pSv_s += total_flux * dcc[ip][ie] * ewid[ie];
        }

    }
    double gcr_dose_uSv_h = gcr_dose_pSv_s * 3600.0 * 1.0e-6;
    cout << gcr_dose_uSv_h << endl;
    return 0;
}