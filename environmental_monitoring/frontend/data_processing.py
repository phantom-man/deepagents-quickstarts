"""
Data Processing Utilities for Environmental Monitoring Dashboard

Statistical analysis, aggregation, and transformation functions.
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import savgol_filter


class DataProcessor:
    """Process and analyze environmental data."""
    
    @staticmethod
    def to_dataframe(data: List[Dict], timestamp_col: str = "timestamp") -> pd.DataFrame:
        """Convert list of dicts to pandas DataFrame."""
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert timestamp column to datetime
        if timestamp_col in df.columns:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
            df.set_index(timestamp_col, inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    @staticmethod
    def resample_timeseries(
        df: pd.DataFrame,
        freq: str = "1H",
        agg_func: str = "mean"
    ) -> pd.DataFrame:
        """Resample time series data to a different frequency."""
        if df.empty:
            return df
        
        agg_functions = {
            "mean": "mean",
            "median": "median",
            "sum": "sum",
            "min": "min",
            "max": "max",
            "std": "std"
        }
        
        return df.resample(freq).agg(agg_functions.get(agg_func, "mean"))
    
    @staticmethod
    def calculate_statistics(data: pd.Series) -> Dict[str, float]:
        """Calculate comprehensive statistics for a data series."""
        if data.empty or data.isna().all():
            return {}
        
        clean_data = data.dropna()
        var_val = clean_data.var()
        
        return {
            "count": len(clean_data),
            "mean": float(clean_data.mean()),  # type: ignore[arg-type]
            "median": float(clean_data.median()),  # type: ignore[arg-type]
            "std": float(clean_data.std()),  # type: ignore[arg-type]
            "min": float(clean_data.min()),  # type: ignore[arg-type]
            "max": float(clean_data.max()),  # type: ignore[arg-type]
            "range": float(clean_data.max() - clean_data.min()),  # type: ignore[arg-type]
            "variance": float(var_val) if var_val is not None else 0.0,  # type: ignore[arg-type]
            "skewness": float(stats.skew(clean_data)),
            "kurtosis": float(stats.kurtosis(clean_data)),
            "p10": float(clean_data.quantile(0.10)),  # type: ignore[arg-type]
            "p25": float(clean_data.quantile(0.25)),  # type: ignore[arg-type]
            "p50": float(clean_data.quantile(0.50)),  # type: ignore[arg-type]
            "p75": float(clean_data.quantile(0.75)),  # type: ignore[arg-type]
            "p90": float(clean_data.quantile(0.90)),  # type: ignore[arg-type]
            "iqr": float(clean_data.quantile(0.75) - clean_data.quantile(0.25))  # type: ignore[arg-type]
        }
    
    @staticmethod
    def detect_anomalies(
        data: pd.Series,
        method: str = "zscore",
        threshold: float = 3.0
    ) -> pd.Series:
        """Detect anomalies in time series data."""
        if data.empty:
            return pd.Series(dtype=bool)
        
        anomalies: pd.Series
        if method == "zscore":
            z_scores = np.abs(stats.zscore(data.dropna().values))  # type: ignore[call-overload]
            anomalies = pd.Series(z_scores > threshold, index=data.dropna().index)
        elif method == "iqr":
            q1, q3 = data.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            anomalies = (data < lower) | (data > upper)
        elif method == "rolling":
            rolling_mean = data.rolling(window=24, min_periods=1).mean()
            rolling_std = data.rolling(window=24, min_periods=1).std()
            anomalies = pd.Series(np.abs(data - rolling_mean) > threshold * rolling_std)
        else:
            anomalies = pd.Series([False] * len(data), index=data.index)
        
        return anomalies
    
    @staticmethod
    def calculate_moving_average(
        data: pd.Series,
        window: int = 24,
        method: str = "simple"
    ) -> pd.Series:
        """Calculate moving average."""
        if data.empty:
            return data
        
        if method == "simple":
            return data.rolling(window=window, min_periods=1).mean()
        elif method == "exponential":
            return data.ewm(span=window, min_periods=1).mean()
        elif method == "weighted":
            weights = np.arange(1, window + 1)
            return data.rolling(window).apply(
                lambda x: np.dot(x, weights[-len(x):]) / weights[-len(x):].sum()
            )
        else:
            return data.rolling(window=window, min_periods=1).mean()
    
    @staticmethod
    def calculate_correlation(
        df: pd.DataFrame,
        method: Literal["pearson", "kendall", "spearman"] = "pearson"
    ) -> pd.DataFrame:
        """Calculate correlation matrix."""
        if df.empty:
            return pd.DataFrame()
        
        numeric_df = df.select_dtypes(include=[np.number])
        return numeric_df.corr(method=method)
    
    @staticmethod
    def calculate_trend(data: pd.Series) -> Dict[str, Any]:
        """Calculate trend using linear regression."""
        if data.empty or len(data) < 2:
            return {"slope": 0, "intercept": 0, "r_squared": 0, "p_value": 1}
        
        clean_data = data.dropna()
        if len(clean_data) < 2:
            return {"slope": 0, "intercept": 0, "r_squared": 0, "p_value": 1}
        
        x = np.arange(len(clean_data))
        y = clean_data.values
        
        # linregress returns a LinregressResult named tuple
        result = stats.linregress(x, y)
        slope_val = float(result[0])  # type: ignore[arg-type]  # slope
        intercept_val = float(result[1])  # type: ignore[arg-type]  # intercept
        r_value_val = float(result[2])  # type: ignore[arg-type]  # rvalue
        p_value_val = float(result[3])  # type: ignore[arg-type]  # pvalue
        std_err_val = float(result[4])  # type: ignore[arg-type]  # stderr
        
        return {
            "slope": slope_val,
            "intercept": intercept_val,
            "r_squared": r_value_val ** 2,
            "p_value": p_value_val,
            "std_err": std_err_val,
            "trend_direction": "increasing" if slope_val > 0 else "decreasing" if slope_val < 0 else "stable"
        }
    
    @staticmethod
    def seasonal_decomposition(
        data: pd.Series,
        period: int = 24
    ) -> Dict[str, pd.Series]:
        """Decompose time series into trend, seasonal, and residual components."""
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        if data.empty or len(data) < 2 * period:
            return {"trend": data, "seasonal": data * 0, "residual": data * 0}
        
        try:
            result = seasonal_decompose(data.dropna(), period=period, extrapolate_trend="freq")
            return {
                "trend": result.trend,
                "seasonal": result.seasonal,
                "residual": result.resid,
                "observed": result.observed
            }
        except Exception:
            return {"trend": data, "seasonal": data * 0, "residual": data * 0}
    
    @staticmethod
    def smooth_data(
        data: pd.Series,
        window: int = 11,
        polyorder: int = 3
    ) -> pd.Series:
        """Smooth data using Savitzky-Golay filter."""
        if data.empty or len(data) < window:
            return data
        
        try:
            clean_data = data.ffill().bfill()
            smoothed = savgol_filter(clean_data.values, window, polyorder)
            return pd.Series(smoothed, index=data.index)
        except Exception:
            return data
    
    @staticmethod
    def calculate_aqi(pm25: float) -> Tuple[int, str, str]:
        """Calculate AQI from PM2.5 concentration."""
        breakpoints = [
            (0, 12.0, 0, 50, "Good", "#00E400"),
            (12.1, 35.4, 51, 100, "Moderate", "#FFFF00"),
            (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "#FF7E00"),
            (55.5, 150.4, 151, 200, "Unhealthy", "#FF0000"),
            (150.5, 250.4, 201, 300, "Very Unhealthy", "#8F3F97"),
            (250.5, 500.4, 301, 500, "Hazardous", "#7E0023")
        ]
        
        for bp_lo, bp_hi, i_lo, i_hi, category, color in breakpoints:
            if bp_lo <= pm25 <= bp_hi:
                aqi = ((i_hi - i_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + i_lo
                return int(round(aqi)), category, color
        
        return 500, "Hazardous", "#7E0023"
    
    @staticmethod
    def join_datasets(
        datasets: List[pd.DataFrame],
        join_key: str = "timestamp",
        how: Literal["left", "right", "outer", "inner", "cross"] = "outer"
    ) -> pd.DataFrame:
        """Join multiple datasets on a common key."""
        if not datasets:
            return pd.DataFrame()
        
        if len(datasets) == 1:
            return datasets[0]
        
        result = datasets[0]
        for df in datasets[1:]:
            if join_key in result.columns and join_key in df.columns:
                result = pd.merge(result, df, on=join_key, how=how)
            elif result.index.name == join_key and df.index.name == join_key:
                result = result.join(df, how=how, rsuffix="_r")
        
        return result
    
    @staticmethod
    def aggregate_by_period(
        df: pd.DataFrame,
        period: str = "D",
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Aggregate data by time period."""
        if df.empty:
            return df
        
        if columns:
            df = df[columns]
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        return df[numeric_cols].resample(period).agg(["mean", "min", "max", "std", "count"])
    
    @staticmethod
    def compare_periods(
        df: pd.DataFrame,
        column: str,
        period1: Tuple[datetime, datetime],
        period2: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Compare statistics between two time periods."""
        if df.empty or column not in df.columns:
            return {}
        
        data1 = df.loc[period1[0]:period1[1], column]
        data2 = df.loc[period2[0]:period2[1], column]
        
        stats1 = DataProcessor.calculate_statistics(data1)
        stats2 = DataProcessor.calculate_statistics(data2)
        
        # Calculate differences
        diff = {}
        for key in stats1:
            if key in stats2 and isinstance(stats1[key], (int, float)):
                diff[key] = stats2[key] - stats1[key]
                if stats1[key] != 0:
                    diff[f"{key}_pct_change"] = ((stats2[key] - stats1[key]) / stats1[key]) * 100
        
        return {
            "period1": {
                "start": period1[0].isoformat() if isinstance(period1[0], datetime) else str(period1[0]),
                "end": period1[1].isoformat() if isinstance(period1[1], datetime) else str(period1[1]),
                "statistics": stats1
            },
            "period2": {
                "start": period2[0].isoformat() if isinstance(period2[0], datetime) else str(period2[0]),
                "end": period2[1].isoformat() if isinstance(period2[1], datetime) else str(period2[1]),
                "statistics": stats2
            },
            "difference": diff
        }


# Singleton instance
data_processor = DataProcessor()
