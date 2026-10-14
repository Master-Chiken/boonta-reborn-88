/* 23-pilot Episode I Racer roster. Values are gameplay-balancing presets,
 * not a claim that all hidden original handling values have been restored. */
#include "vehicle_catalog.h"

static const RacerVehicleSpec g_vehicles[RACER_VEHICLE_COUNT] = {
    /* name, speed, accel, steering, grip, boost, heat, cooling, drift, resistance, RGB */
    {"ANAKIN",          51.0f,20.8f,1.04f,1.10f,25.5f,31.0f,21.0f,13.0f,0.95f,236,166,55},
    {"SEBULBA",         54.0f,19.2f,0.92f,0.88f,29.0f,37.0f,16.0f,10.0f,0.90f,213,62,45},
    {"RATTS TYERELL",   45.0f,22.8f,1.25f,1.22f,22.0f,26.0f,25.0f,17.0f,1.22f,84,194,111},
    {"TEEMTO PAGALIES", 49.0f,21.2f,1.13f,1.07f,24.0f,29.0f,22.0f,15.0f,1.00f,74,158,214},
    {"MAWHONIC",        48.0f,19.4f,1.02f,1.17f,27.0f,30.0f,23.0f,14.0f,1.08f,179,116,221},
    {"DUD BOLT",        56.0f,18.3f,0.86f,0.84f,27.0f,35.0f,17.0f,10.0f,0.78f,214,192,84},
    {"GASGANO",         53.0f,20.0f,0.98f,0.96f,27.0f,33.0f,19.0f,12.0f,0.91f,74,174,224},
    {"ALDAR BEEDO",     50.0f,21.0f,1.12f,1.04f,24.0f,30.0f,21.0f,14.0f,1.02f,206,89,67},
    {"CLEGG HOLDFAST",  47.0f,22.0f,1.18f,1.14f,23.0f,28.0f,23.0f,15.0f,1.13f,213,154,83},
    {"ELAN MAK",        52.0f,20.5f,1.01f,1.00f,26.0f,32.0f,20.0f,13.0f,0.94f,130,194,127},
    {"EBE ENDOCOTT",    46.0f,22.4f,1.21f,1.16f,22.0f,27.0f,24.0f,16.0f,1.18f,222,173,89},
    {"ARK ROOSE",       48.0f,21.5f,1.08f,1.11f,24.0f,29.0f,22.0f,14.0f,1.05f,163,118,84},
    {"NEVA KEE",        55.0f,18.9f,0.91f,0.89f,28.0f,36.0f,17.0f,10.0f,0.84f,224,106,151},
    {"WAN SANDAGE",     49.0f,21.8f,1.10f,1.06f,24.0f,30.0f,21.0f,14.0f,1.00f,109,178,206},
    {"BOLES ROOR",      44.0f,23.0f,1.24f,1.20f,21.0f,26.0f,25.0f,17.0f,1.20f,199,144,97},
    {"BEN QUADINAROS",  43.0f,23.4f,1.28f,1.25f,21.0f,25.0f,26.0f,18.0f,1.25f,133,188,111},
    {"ODY MANDRELL",    50.0f,20.4f,1.05f,1.03f,25.0f,31.0f,21.0f,13.0f,1.01f,230,181,79},
    {"MARS GUO",        52.0f,20.0f,1.00f,0.98f,27.0f,33.0f,19.0f,12.0f,0.93f,202,115,194},
    {"TOY DAMP",     47.0f,21.7f,1.16f,1.12f,23.0f,28.0f,23.0f,15.0f,1.10f,105,154,214},
    {"BOZZIE BARANTA",  48.0f,21.0f,1.09f,1.08f,24.0f,29.0f,22.0f,14.0f,1.04f,188,143,84},
    {"SLIDE PARAMITA",  51.0f,20.3f,1.03f,1.01f,26.0f,32.0f,20.0f,13.0f,0.97f,119,190,183},
    {"FUD SANG",        46.0f,22.2f,1.19f,1.15f,22.0f,27.0f,24.0f,16.0f,1.16f,176,134,207},
    {"CY YUNGA",        57.0f,18.1f,0.84f,0.82f,28.0f,37.0f,16.0f,9.0f,0.80f,221,207,127}
};

const RacerVehicleSpec *vehicle_catalog_get(unsigned int index)
{ return index < RACER_VEHICLE_COUNT ? &g_vehicles[index] : &g_vehicles[0]; }
unsigned int vehicle_catalog_count(void) { return RACER_VEHICLE_COUNT; }
