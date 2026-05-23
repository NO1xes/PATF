# configs/

Station network configuration files.

Each file describes a sensor network: station IDs, coordinates, data frequency, and expected variables.

## Format

```yaml
network_id: example_network
stations:
  - id: STA001
    lat: 39.92
    lon: 116.46
    elevation_m: 50
    variables: [temp_c, precip_mm, wind_ms]
    freq_min: 10
```
