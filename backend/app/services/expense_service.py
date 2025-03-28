# backend/app/services/expense_service.py
from ..database import db # Opravený relatívny import
from ..models.expense import Expense # Opravený relatívny import
# import logging

# logger = logging.getLogger(__name__)

class ExpenseServiceError(Exception):
    """Vlastná výnimka pre chyby v servisnej vrstve."""
    pass

class ExpenseNotFoundError(ExpenseServiceError):
    """Výnimka pre prípad, že výdavok nebol nájdený."""
    pass

class ExpenseService:
    @staticmethod
    def get_all_expenses():
        """Získa všetky výdavky zoradené podľa dátumu."""
        try:
            return Expense.query.order_by(Expense.date_created.desc()).all()
        except Exception as e:
            print(f"Database error retrieving expenses: {e}")
            raise ExpenseServiceError("Nepodarilo sa načítať výdavky z databázy.") from e

    @staticmethod
    def add_new_expense(new_expense_object): # Premenuj parameter pre jasnoť
        """
        Pridá nový výdavok (už ako objekt Expense) do databázy.
        Predpokladá, že objekt bol vytvorený a validovaný schémou.
        """
        # Objekt už máme, nemusíme ho vytvárať znova
        # new_expense = Expense(...) # <<< TOTO ODSTRÁNIME

        try:
            # Priamo pridáme existujúci objekt do session
            db.session.add(new_expense_object)
            db.session.commit()
            # logger.info(f"Expense added: ID={new_expense_object.id}")
            return new_expense_object # Vrátime uložený objekt (teraz už má aj ID)
        except Exception as e:
            db.session.rollback()
            # logger.error(f"Database error adding expense: {e}", exc_info=True)
            print(f"Database error adding expense: {e}")
            raise ExpenseServiceError("Nepodarilo sa pridať výdavok do databázy.") from e
    
    @staticmethod
    def update_expense(expense_id, update_payload): # Názov parametra zodpovedá tomu z routy
        """
        Aktualizuje existujúci výdavok podľa ID.
        'update_payload' je objekt Expense vytvorený a validovaný schémou.
        """
        try:
            # 1. Nájdi objekt, ktorý chceme aktualizovať v DB
            expense_to_update = ExpenseService.get_expense_by_id(expense_id)

            # 2. Skopíruj validované hodnoty z 'update_payload' objektu
            #    na objekt 'expense_to_update', ktorý je pripojený k DB session.
            expense_to_update.description = update_payload.description # <-- Použi bodku
            expense_to_update.amount = update_payload.amount           # <-- Použi bodku

            # Pre kategóriu: Schéma zabezpečí, že 'category' existuje v objekte,
            # ak bola v JSONe alebo má default (môže byť aj None, ak allow_none=True).
            # Jednoducho prenesieme hodnotu. DB si poradí s None alebo použije svoj default.
            if hasattr(update_payload, 'category'): # Iba ak schéma pole naozaj obsahuje
                 expense_to_update.category = update_payload.category # <-- Použi bodku
            # else:
                 # Ak by sme chceli explicitne nastaviť default, ak kategória nebola poslaná:
                 # expense_to_update.category = 'Nezaradené' # Alebo None, ak DB default je null


            # 3. Ulož zmeny do DB (SQLAlchemy sleduje zmeny na 'expense_to_update')
            db.session.commit()
            # logger.info(f"Expense updated: ID={expense_id}")
            return expense_to_update # Vráti aktualizovaný (už uložený) objekt
        except ExpenseNotFoundError:
             # Ak get_expense_by_id vyvolal chybu
             raise
        except Exception as e:
            db.session.rollback() # Rollback pri akejkoľvek chybe počas update
            # logger.error(f"Database error updating expense ID {expense_id}: {e}", exc_info=True)
            print(f"Database error updating expense ID {expense_id}: {e}")
            raise ExpenseServiceError(f"Nepodarilo sa aktualizovať výdavok s ID {expense_id}.") from e
    @staticmethod
    def delete_expense_by_id(expense_id):
        """Vymaže výdavok podľa ID."""
        try:
            # Nájdi výdavok (vyvolá chybu ak nenájde, čo je OK)
            expense_to_delete = ExpenseService.get_expense_by_id(expense_id)
            # Vymaž objekt zo session
            db.session.delete(expense_to_delete)
            # Potvrď zmeny v DB
            db.session.commit()
            # logger.info(f"Expense deleted: ID={expense_id}")
            return True # Signalizuj úspech
        except ExpenseNotFoundError:
             # Ak get_expense_by_id vyvolal chybu, len ju posielame ďalej
             raise
        except Exception as e:
            db.session.rollback() # Dôležitý rollback pri chybe
            # logger.error(f"Database error deleting expense ID {expense_id}: {e}", exc_info=True)
            print(f"Database error deleting expense ID {expense_id}: {e}")
            raise ExpenseServiceError(f"Nepodarilo sa vymazať výdavok s ID {expense_id}.") from e
    @staticmethod
    def get_expense_by_id(expense_id):
         """Získa jeden výdavok podľa ID."""
         try:
             # Použi get_or_404 pre automatické vrátenie 404 ak nenájde
             # expense = Expense.query.get_or_404(expense_id)
             # Alebo manuálne pre vlastnú výnimku:
             expense = db.session.get(Expense, expense_id) # Preferovaný spôsob pre get by primary key v SQLAlchemy 1.4+
             if not expense:
                 raise ExpenseNotFoundError(f"Výdavok s ID {expense_id} nebol nájdený.")
             return expense
         except ExpenseNotFoundError:
             raise
         except Exception as e:
             print(f"Database error retrieving expense ID {expense_id}: {e}")
             raise ExpenseServiceError(f"Chyba pri načítaní výdavku s ID {expense_id}.") from e