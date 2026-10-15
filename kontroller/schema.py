import pandera.pandas as pa

REGIONER = ["Väst", "Norr", "Stockholm", "Syd", "Mitt"]
ABONNEMANG = ["Bas", "Premium", "Standard"]

SCHEMA = pa.DataFrameSchema(
    {
        "kund_id": pa.Column(int, unique=True),
        "alder": pa.Column(int, pa.Check.in_range(18, 110)),
        "region": pa.Column(str, pa.Check.isin(REGIONER)),
        "manader_som_kund": pa.Column(int, pa.Check.ge(0)),
        "abonnemang": pa.Column(str, pa.Check.isin(ABONNEMANG)),
        "manadskostnad": pa.Column(float, pa.Check.gt(0.0)),
        "data_gb_per_manad": pa.Column(float, pa.Check.ge(0.0)),
        "supportarenden_12m": pa.Column(int, pa.Check.ge(0)),
        "avslutat": pa.Column(int, pa.Check.isin([0, 1])),
    },
    strict=True,
)


def validate_data(df):
    return SCHEMA.validate(df, lazy=True)
