# hass-samsung-mimb19n
Home assistant samsung mim-b19n module integration

## Building Docker image

``` docker build -t hass-samsung-mimb19n:latest . ```

## Running docker image

``` docker run --rm --env MQTT_BROKER=192.168.1.204 --env MIM_B19N_DEVICE=192.168.1.46 hass-samsung-mimb19n:latest ```

### For testing purposes

``` docker run -it --rm --env MQTT_BROKER=192.168.1.204 --env MIM_B19N_DEVICE=192.168.1.46 hass-samsung-mimb19n:latest ```