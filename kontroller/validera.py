import pandas as pd
import pandera.pandas as pa

from kontroller.schema import SCHEMA


def main(fil: str) -> int:
    df = pd.read_csv(fil)

    try:
        SCHEMA.validate(df, lazy=True)

    except pa.errors.SchemaErrors as e:
        print(f"STOPP: {fil} klarar inte schemat")
        print(e.failure_cases)
        return 1

    print(f"OK: {fil} ({len(df)} rader)")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1]))
