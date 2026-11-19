import re

def parse_phase_1_data(data_lines):
    phase_1_data = []
    in_phase = False
    new_section = True
    for line in data_lines:
        if "Entering Phase 1" in line:
            if new_section:  # Add separator for new section except for the first one
                if phase_1_data:
                    phase_1_data.append("\n---\n")
            in_phase = True
            new_section = False
        elif "Entering Phase" in line and in_phase:
            in_phase = False
            new_section = True  # Prepare for a new section
        elif in_phase:
            match = re.match(r"\{(\d+),(\d+),(\d+),(.+)\}", line)
            if match:
                timestamp, phase, data_type, data = match.groups()
                if int(phase) == 1:
                    if int(data_type) == 0:  # Position
                        lat, lon, _ = map(float, re.findall(r"-?\d+\.?\d*", data))
                        phase_1_data.append(f"Latitude\t{lat:.2f}\n")
                        phase_1_data.append(f"Longitude\t{lon:.2f}\n")
                    elif int(data_type) == 1:  # Rotation
                        _, pitch, _ = map(float, re.findall(r"-?\d+\.?\d*", data))
                        phase_1_data.append(f"Attitude (Pitch)\t{pitch:.2f} (Deg)\n")
                        phase_1_data.append("\n---\n")
    if phase_1_data and phase_1_data[-1] == "\n---\n":
        phase_1_data.pop()  # Remove last "---" if exists
    return phase_1_data

def parse_phase_2_data(data_lines):
    phase_2_data = []
    in_phase = False
    current_instance = {
        "Location": [chr(65 + i) for i in range(25)],  # Locations from A to Y
        "Temperature": [25] * 25,
        "Status": ["Location is Safe"] * 25
    }
    for line in data_lines:
        if "Entering Phase 2" in line:
            if in_phase:
                phase_2_data.append(format_phase_2_instance(current_instance))
                phase_2_data.append("\n---\n")
            in_phase = True
            current_instance = {
                "Location": [chr(65 + i) for i in range(25)],  # Locations from A to Y
                "Temperature": [25] * 25,
                "Status": ["Location is Safe"] * 25
            }
            phase_2_data.append("Location\tTemperature\tStatus\n")
        elif "Entering Phase" in line and in_phase:
            in_phase = False
            phase_2_data.append(format_phase_2_instance(current_instance))
            phase_2_data.append("\n---\n")
        elif in_phase:
            match = re.match(r"\{(\d+),(\d+),(\d+),(.+)\}", line)
            if match:
                timestamp, phase, data_type, data = match.groups()
                if int(phase) == 2:
                    if int(data_type) == 0:  # Classifications
                        classifications = eval(data)
                        index = 0
                        for row in classifications:
                            for value in row:
                                location = chr(65 + index)
                                temperature = 25  # Default temperature, adjust as necessary
                                status = "Location is Safe"
                                if value == 2:
                                    status = "Location on Fire"
                                elif value == 0:
                                    status = "Evacuate"
                                current_instance["Location"][index] = location
                                current_instance["Temperature"][index] = temperature
                                current_instance["Status"][index] = status
                                index += 1
                    elif int(data_type) == 1:  # Grid Temperatures
                        temperatures = eval(data)
                        index = 0
                        for row in temperatures:
                            for temp in row:
                                if index < 25:
                                    current_instance["Temperature"][index] = temp
                                index += 1
    if in_phase:
        phase_2_data.append(format_phase_2_instance(current_instance))
    if phase_2_data and phase_2_data[-1] == "\n---\n":
        phase_2_data.pop()  # Remove last "---" if exists
    return phase_2_data

def format_phase_2_instance(instance):
    formatted_instance = ""
    for i in range(25):
        formatted_instance += f"{instance['Location'][i]}\t{instance['Temperature'][i]:.2f} C\t{instance['Status'][i]}\n"
    return formatted_instance

def parse_phase_3_data(data_lines):
    phase_3_data = []
    in_phase = False
    current_instance = {
        "Location": [chr(65 + i) for i in range(25)],  # Locations from A to Y
        "Temperature": [25] * 25
    }
    for line in data_lines:
        if "Entering Phase 3" in line:
            in_phase = True
        elif "Entering Phase" in line and in_phase:
            in_phase = False
        elif in_phase:
            match = re.match(r"\{(\d+),(\d+),(\d+),(.+)\}", line)
            if match:
                timestamp, phase, data_type, data = match.groups()
                if int(phase) == 3 and int(data_type) == 7:  # Grid Temperatures for phase 3
                    temperatures = eval(data)
                    hottest_grid_location, max_temp = find_hottest_grid(temperatures)
                    phase_3_data.append(f"Timestamp: {timestamp}, Hottest Grid Location: {hottest_grid_location}, Temperature: {max_temp:.2f} C\n")
    return phase_3_data

def find_hottest_grid(temperatures):
    max_temp = -float('inf')
    hottest_grid_location = None
    for i, row in enumerate(temperatures):
        for j, temp in enumerate(row):
            if temp > max_temp:
                max_temp = temp
                hottest_grid_location = chr(65 + i * 5 + j)  # Convert index to corresponding letter
    return hottest_grid_location, max_temp

def save_phase_data(file_path, phase_data):
    with open(file_path, 'w') as file:
        for line in phase_data:
            file.write(line)

def main():
    # Input file containing all phases
    input_file_path = input("Enter logfile to translate:")  # Replace with the actual path to your input file

    with open(input_file_path, 'r') as file:
        data_lines = file.readlines()

    # Process and save data for each phase
    phase_1_data = parse_phase_1_data(data_lines)
    save_phase_data('output_phase_1.txt', phase_1_data)

    phase_2_data = parse_phase_2_data(data_lines)
    save_phase_data('output_phase_2.txt', phase_2_data)

    phase_3_data = parse_phase_3_data(data_lines)
    save_phase_data('output_phase_3.txt', phase_3_data)

    print("Data for all phases have been extracted and saved.")

if __name__ == "__main__":
    main()
