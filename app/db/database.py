from sqlmodel import SQLModel, create_engine, Session, select
from app.config import DB_PATH
from app.db.models import CategoryRule, CardMapping


# SQLite database URL
sqlite_url = f"sqlite:///{DB_PATH}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def init_db():
    """Create all tables and seed default category rules and card mappings if empty."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        existing_rules = session.exec(select(CategoryRule)).all()
        if not existing_rules:
            default_rules = [
                CategoryRule(pattern="(?i)shufersal|rami levy|victory|yohananof|osher ad|mega|tiv taam|carrefour", category="Groceries"),
                CategoryRule(pattern="(?i)super-pharm|be|pharmacy", category="Health & Pharmacy"),
                CategoryRule(pattern="(?i)paz|sonol|delek|ten|dor alon|yellow|waze", category="Transportation & Fuel"),
                CategoryRule(pattern="(?i)mcdonalds|aroma|burger|cafe|restaurant|wolt|tenbis|pizza", category="Dining & Cafe"),
                CategoryRule(pattern="(?i)netflix|spotify|apple|google|youtube|disney|prime", category="Subscriptions"),
                CategoryRule(pattern="(?i)iec|electric|arnona|water|gash|bezeq|hot|partner|cellcom|pelephone", category="Utilities & Bills"),
                CategoryRule(pattern="(?i)zara|h&m|castro|fox|renuar|shoes|clothing|nike|adidas", category="Apparel & Shopping"),
            ]
            for rule in default_rules:
                session.add(rule)
            session.commit()
            
        existing_cards = session.exec(select(CardMapping)).all()
        if not existing_cards:
            card_defaults = [
                CardMapping(card_last_4='9380', institution='CAL', owner_name='Rani', display_name='Rani CAL'),
                CardMapping(card_last_4='4591', institution='Leumicard', owner_name='Rani', display_name='Rani Leumicard'),
                CardMapping(card_last_4='4656', institution='Isracard', owner_name='Yael', display_name='Yael Mastercard'),
                CardMapping(card_last_4='1123', institution='Max', owner_name='Yael', display_name='Yael Max'),
            ]
            for c in card_defaults:
                session.add(c)
            session.commit()



def get_session():
    with Session(engine) as session:
        yield session
