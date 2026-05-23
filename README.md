# PATF

**Precipitation and Atmospheric Time-series Framework**

Early-stage personal project for working with meteorological time-series data from weather station networks. Not ready for general use.

---

## Rough Scope

- Reading raw sensor output from station networks
- Aligning and gap-filling time-series across data sources
- Basic aggregation (daily/monthly summaries)

No stable API yet. Structure will change.

---

## Layout (in progress)

```
patf/
  io/          reading sensor data
  align/       time alignment (stub)
  stats/       aggregation (not started)
configs/       example station configs
docs/          working notes
```

---

## Dependencies

Python 3.10+, numpy, pandas. No install script yet.
