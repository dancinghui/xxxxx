import os

def main():
    folders = os.listdir("detail")
    count = 0
    for folder in folders:
        files = os.listdir("detail/" + folder)
        count += len(files)

    print count

if __name__ == '__main__':
    main()