from pydantic import BaseModel, Field, model_validator

class MarketData(BaseModel):
    market_name: str
    quota: float = Field(..., gt=1.01, description="La quota deve essere > 1.01")
    probabilita_reale: float = Field(..., ge=0.0, le=1.0, description="Probabilità tra 0.0 e 1.0")
    
    @property
    def edge(self) -> float:
        return round((self.probabilita_reale * self.quota) - 1.0, 4)

class MatchContext(BaseModel):
    fixture_id: str
    home_team: str
    away_team: str
    sesto_senso_validated: bool = Field(False)
    injuries_checked: bool = Field(False)
    lineup_confirmed: bool = Field(False)

    @model_validator(mode='after')
    def check_pipeline_gates(self) -> 'MatchContext':
        if not self.injuries_checked:
            raise ValueError("Violazione Gate 2: Controllo infortuni/assenze non eseguito.")
        return self
