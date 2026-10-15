import unittest

from risk_engine import calculate_risk, detect_sentiment


class RiskEngineTests(unittest.TestCase):
    def test_high_risk_combines_all_documented_factors(self) -> None:
        assessment = calculate_risk(
            message="Estou muito cansada e não vou conseguir ir amanhã.",
            age=72,
            prior_no_shows=2,
            days_until_appointment=1,
        )
        self.assertEqual(assessment.score, 100)
        self.assertEqual(assessment.level, "ALTO")
        self.assertEqual(assessment.action, "LIGACAO_PRIORITARIA")

    def test_medium_risk_uses_negative_message_and_near_appointment(self) -> None:
        assessment = calculate_risk(
            message="Talvez eu não consiga ir.", age=68,
            prior_no_shows=0, days_until_appointment=2,
        )
        self.assertEqual(assessment.score, 55)
        self.assertEqual(assessment.level, "MEDIO")
        self.assertEqual(assessment.action, "LEMBRETE_REFORCADO")

    def test_confirmed_appointment_is_low_risk_when_other_factors_absent(self) -> None:
        assessment = calculate_risk(
            message="Confirmo minha presença.", age=65,
            prior_no_shows=0, days_until_appointment=5,
        )
        self.assertEqual(detect_sentiment("Confirmo minha presença."), "POSITIVO")
        self.assertEqual(assessment.score, 0)
        self.assertEqual(assessment.level, "BAIXO")


if __name__ == "__main__":
    unittest.main()
