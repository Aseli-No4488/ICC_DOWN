from src.server import main as server

if not __name__ == '__main__':
    print("Please run this script as main.")
    exit()

# Check the path of process and the path of this file
import os
filepath = os.path.dirname(os.path.abspath(__file__))

# Move the cursor to the same path as this file
os.chdir(filepath)

processpath = os.path.abspath(os.getcwd())

if filepath != processpath:
    print('Please run this script in the same path as this file.')
    exit()


# Run server
server()