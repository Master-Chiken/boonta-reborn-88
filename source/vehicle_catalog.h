#ifndef SWE1R_VEHICLE_CATALOG_H
#define SWE1R_VEHICLE_CATALOG_H

#include "racer_physics.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Full 23-pilot roster represented by distinct gameplay tuning presets. */
#define RACER_VEHICLE_COUNT 23U

const RacerVehicleSpec *vehicle_catalog_get(unsigned int index);
unsigned int vehicle_catalog_count(void);

#ifdef __cplusplus
}
#endif
#endif
