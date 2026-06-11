# Week 13 ML Summary

## Task

Predict Tokyo temperature for the next hour. Features contain only information
available at hour `t`; the target is temperature at hour `t+1`.

## Leakage Protection

- target is shifted one hour into the future and is not included in features;
- rows are sorted by timestamp;
- the first 80% of observations form train and the last 20% form test;
- no preprocessing is fitted on the test set.

## Data Split

- input rows: 167
- train rows: 133, period: 2024-05-01 00:00:00 to 2024-05-06 12:00:00
- test rows: 34, period: 2024-05-06 13:00:00 to 2024-05-07 22:00:00
- features: temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m, hour_sin, hour_cos

## Metrics

| Model | MAE | RMSE | R2 |
|---|---:|---:|---:|
| Baseline | 2.6354 | 2.7674 | -9.7379 |
| Linear Regression | 0.7265 | 0.8429 | 0.0038 |

MAE is the average absolute prediction error in degrees Celsius. RMSE penalizes
large errors more strongly. R2 compares the model with prediction by the test
mean; values below zero indicate poor generalization.

## Conclusion

Linear Regression is better than the mean baseline by MAE. However, R2 is close to zero, so the model explains almost none of
the variation beyond a constant prediction. The dataset covers only seven days,
so metrics are not stable enough for production use. More historical data and
comparison with a stronger time-series baseline are required.
