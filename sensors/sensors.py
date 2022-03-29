import csv


def create_csv_file(header: str, d: list, index: int):
    if not d:
        return

    data = []
    for row in d:
        data.append(",".join(row))

    with open(f"/data/{index}.csv", "w") as f:
        f.writelines(",".join(header))
        f.write("\n")
        f.writelines("\n".join(data))

def main():
    # NOTE: to change
    chunk_size = 1000
    line_numbers = 0
    header = []

    with open("/data/dataset_MP.csv") as f:

        list_data = list(csv.reader(f, delimiter=","))
        line_numbers = len(list_data)

        header = list_data.pop(0)

        index = 0
        for i in range(0, line_numbers, chunk_size):
            create_csv_file(header, list_data[i : i + chunk_size], index)
            index += 1


if __name__ == "__main__":
    main()