import subprocess
import argparse
import os

if __name__ == '__main__':
    def add_command(filename, command):
        filename.write(command+'\n')

    def append_command(command, new_command):
        return command + ' && ' + new_command

    parser = argparse.ArgumentParser()
    parser.add_argument('path_to_main_folder', help='where I should store the output')
    parser.add_argument('path_to_commands_file_name', help='the name and place of the commands file')
    parser.add_argument('amount', help='how many folders to make (experiment amount)', type=int)
    parser.add_argument('amount2', help='how many things to put in each folder', type=int)
    args = parser.parse_args()
    path_to_commands_file_name = os.path.abspath(args.path_to_commands_file_name)
    path_to_main_folder = os.path.abspath(args.path_to_main_folder)
    amount = args.amount
    amount2 = args.amount2
    # create the folder
    subprocess.run('mkdir {}'.format(path_to_main_folder), shell=True)
    # create the commands file
    subprocess.run('touch {}'.format(path_to_commands_file_name), shell=True)

    with open(path_to_commands_file_name, 'w') as commands_file:
        for experiment_number in range(amount):
            command = 'cd "{}"'.format(path_to_main_folder)
            output_folder = 'output_dir_{}'.format(experiment_number)
            command = append_command(command, 'mkdir "{}"'.format(output_folder))
            command = append_command(command, 'cd "{}"'.format(output_folder))
            for output_number in range(amount2):
                filename = 'file_number_{}_{}.txt'.format(output_number, experiment_number)
                # create a file for the output
                command = append_command(command, 'touch "{}"'.format(filename))
                # run the program that will produce the output
                command = append_command(command, 'echo "hello world {}_{}" > "{}"'.format(output_number, experiment_number, filename))
            add_command(commands_file, command)
