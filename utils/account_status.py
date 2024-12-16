import polars as pl
import os
from .plate_normalizer import normalize_plate
from models.account import Account
from .is_similar_plate import is_similar_plate
from typing import List


class AccountStatus:
    def __init__(
        self, 
        path: str,
        normalized_column_name: str = "plate_number_normalized".upper()
    ):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Error: Cannot load {path} as dataframe")

        self.normalized_column_name = normalized_column_name

        self.path = path

        self._account_table = pl.read_csv(path)

        self.__preprocess_dataframe()


    def update_account_records(
        self,
        dataframe: pl.DataFrame
    ):
        if len(dataframe) == 0:
            raise ValueError("Dataframe is empty!")

        self._account_table = dataframe
        
        self.__preprocess_dataframe()

    
    def __preprocess_dataframe(self): 
        if self.normalized_column_name not in self._account_table.columns:
            print("Preprocessing accounts dataframe...")
            # for idx, row in enumerate(self._account_table.iter_rows()):
            self._account_table = self._account_table.with_columns(
                pl.col("PLATE")
                    .map_elements(lambda plate: normalize_plate(plate), return_dtype=str)
                    .alias(self.normalized_column_name)
            )
            self._account_table.write_csv(self.path)
            
    
    def get_account_info_by_plate(self, target_plate: str) -> Account | None:
        matching_rows = self._account_table.filter(
            pl.col("PLATE_NUMBER_NORMALIZED") == target_plate
        ).sort("ENDO_DATE", descending=True)

        if matching_rows.height == 0:
            return None

        latest_account = self.row_to_dict(
            self._account_table.columns,
            matching_rows.row(0)
        )

        return Account(
            plate=latest_account["PLATE"],
            car_model=latest_account["CAR_MODEL"],
            ch_code=latest_account["CH_CODE"],
            client=latest_account["CLIENT"],
            endo_date=latest_account["ENDO_DATE"],
            plate_number_normalized=latest_account["PLATE_NUMBER_NORMALIZED"]
        )
    
    
    def get_similar_accounts_by_plate(
        self,
        target_plate: str
    ) -> List[Account]:
        similar_accounts_df = self._account_table.with_columns(
            pl.col("PLATE_NUMBER_NORMALIZED")
                .map_elements(lambda plate: is_similar_plate(target_plate, plate), return_dtype=bool)
                .alias("is_similar")
        )

        similar_accounts_df = similar_accounts_df.filter(
            pl.col("is_similar") == True
        )

        similar_accounts_df = similar_accounts_df.drop("is_similar")

        top_3_accounts_rows = similar_accounts_df.rows()

        top_3_accounts = [
            self.row_to_dict(
                self._account_table.columns,
                row
            ) for row in top_3_accounts_rows
        ]

        return [
            Account(
                plate=similar_account["PLATE"],
                car_model=similar_account["CAR_MODEL"],
                ch_code=similar_account["CH_CODE"],
                client=similar_account["CLIENT"],
                endo_date=similar_account["ENDO_DATE"],
                plate_number_normalized=similar_account["PLATE_NUMBER_NORMALIZED"]
            ) for similar_account in top_3_accounts
        ]

    
    def row_to_dict(self, columns, row):
        return dict(zip(columns, row))



        
