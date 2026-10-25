"""tests/unit/test_metrics.py — calorie estimator and GPS processor tests."""
import pytest
from features.metrics.tracker import CalorieEstimator, GPSProcessor, GPSPoint, SimulatedSensor
from datetime import datetime


class TestCalorieEstimator:
    @pytest.fixture
    def estimator(self):
        return CalorieEstimator()

    def test_met_lookup_exact(self, estimator):
        met = estimator.estimate_met("running", "easy")
        assert met == pytest.approx(8.0)

    def test_met_lookup_fuzzy(self, estimator):
        met = estimator.estimate_met("yoga")
        assert met > 0

    def test_met_lookup_unknown_returns_default(self, estimator):
        met = estimator.estimate_met("unicycle_polo")
        assert met == pytest.approx(4.0)

    def test_calories_from_met(self, estimator):
        # 70kg person, 60 min at MET 8 = 560 kcal
        cals = estimator.calories_from_met(8.0, 70.0, 60.0)
        assert cals == pytest.approx(560.0, rel=0.01)

    def test_calories_from_hr_male(self, estimator):
        cals = estimator.calories_from_hr(avg_hr=150, age=30, weight_kg=75,
                                           duration_minutes=30, is_male=True)
        assert cals > 0

    def test_calories_from_hr_not_negative(self, estimator):
        cals = estimator.calories_from_hr(avg_hr=40, age=20, weight_kg=50,
                                           duration_minutes=10, is_male=False)
        assert cals >= 0


class TestGPSProcessor:
    @pytest.fixture
    def processor(self):
        return GPSProcessor()

    def test_haversine_known_distance(self, processor):
        # London to Paris ≈ 340 km
        london = GPSPoint(lat=51.5074, lng=-0.1278)
        paris  = GPSPoint(lat=48.8566, lng=2.3522)
        dist = processor.haversine_km(london, paris)
        assert 330 < dist < 360

    def test_same_point_is_zero(self, processor):
        p = GPSPoint(lat=12.0, lng=77.0)
        assert processor.haversine_km(p, p) == pytest.approx(0.0, abs=1e-6)

    def test_total_distance_two_points(self, processor):
        track = [GPSPoint(51.5, -0.1), GPSPoint(51.51, -0.1)]
        dist = processor.total_distance_km(track)
        assert 1.0 < dist < 1.2   # ~1.1 km

    def test_total_distance_empty_track(self, processor):
        assert processor.total_distance_km([]) == 0.0

    def test_elevation_gain_positive_only(self, processor):
        track = [
            GPSPoint(0, 0, 100), GPSPoint(0, 0, 120),
            GPSPoint(0, 0, 110), GPSPoint(0, 0, 130),
        ]
        gain = processor.elevation_gain_m(track)
        assert gain == pytest.approx(40.0)   # 20 up + 20 up; 10 down ignored

    def test_pace_calculation(self, processor):
        # 5 km in 25 min = 5 min/km
        pace = processor.pace_min_per_km(5.0, 25 * 60)
        assert pace == pytest.approx(5.0, rel=0.01)


class TestSimulatedSensor:
    @pytest.fixture
    def sensor(self):
        return SimulatedSensor(height_m=1.75, weight_kg=70)

    def test_steps_to_distance(self, sensor):
        # 1000 steps × 0.413 × 1.75 / 1000 ≈ 0.72 km
        dist = sensor.steps_to_distance_km(1000)
        assert 0.7 < dist < 0.75

    def test_hr_from_breathing(self, sensor):
        hr = sensor.estimate_hr_from_breathing(20)
        assert hr == 80

    def test_hr_clamped(self, sensor):
        assert sensor.estimate_hr_from_breathing(100) == 200  # max
        assert sensor.estimate_hr_from_breathing(1) == 50     # min (4×1=4, clamped to 50)
