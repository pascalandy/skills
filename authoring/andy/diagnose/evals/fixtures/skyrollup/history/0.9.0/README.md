# skyrollup

The nightly daily summary for the Fernlow Weather Network.

Every night at 02:00 UTC a systemd timer on `wx-1` runs `skyrollup run`. It fetches the previous UTC day's readings for each station from the collector, computes per-station and network figures, and publishes them for the website:

- `/srv/www/summaries/summary-YYYY-MM-DD.json`, one file per day
- `/srv/www/summaries/summary-latest.json`, a symlink to the newest day, which the website reads
- `/var/lib/skyrollup/status.json`, read by `skyrollup status`

Stations without readings for the day are logged as offline and left out of the summary.

## Commands

```
python3 -m skyrollup run       # summarize the previous UTC day and publish it
python3 -m skyrollup status    # version and status.json
```

The job logs to `/var/log/skyrollup/skyrollup.log`.

The config file is `/etc/skyrollup/config.toml`, or the path in `SKYROLLUP_CONFIG`. `config.toml` in this repository is the one deployed on `wx-1`.

## Install on wx-1

```
sudo useradd --system --user-group --groups www skyrollup
sudo install -d -o skyrollup -g www -m 0775 /srv/www/summaries
sudo install -d -o skyrollup -g skyrollup /var/lib/skyrollup /var/log/skyrollup
sudo install -d /opt/skyrollup /etc/skyrollup
sudo cp -r skyrollup /opt/skyrollup/ && sudo cp config.toml /etc/skyrollup/
sudo cp systemd/skyrollup.service systemd/skyrollup.timer /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now skyrollup.timer
```
