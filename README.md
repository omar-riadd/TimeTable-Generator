
# 🎓 Automated Timetable Generator (CSP-Based)

## 📘 Overview

This project is an **Automated Timetable Generator** designed for university departments.  
It automatically schedules courses for multiple sections, assigning **rooms**, **instructors**, and **time slots** while satisfying all necessary constraints.

The project is built using Python and applies **Constraint Satisfaction Problem (CSP)** techniques — specifically a **backtracking search algorithm** — to produce conflict-free timetables.

---

## 🧠 Key Idea

The goal is to assign:

(Section, Course) → (TimeSlot, Room, Instructor)

so that:
- No **instructor**, **room**, or **section** is double-booked.
- Instructors only teach their **qualified courses**.
- Courses are scheduled in suitable **room types** (Lab or Classroom).
- Classes respect **instructor unavailability** and **time slot constraints**.
- Schedules are balanced and realistic (no overloaded days or too early classes).

---
## ⚙️ Features

✅ Generates a complete timetable automatically using **CSP + backtracking**  
✅ Detects and fixes missing or incomplete data (e.g., missing classrooms or qualifications)  
✅ Supports **Excel** and **CSV** data input  
✅ Exports results to:
- **CSV file**
- **SQLite database**  
✅ Includes **performance evaluation** (constraint violations, success rate, etc.)  
✅ Provides an **interactive command-line interface (CLI)**  

---



---

## 📂 Input Data Requirements

The system expects **five sheets or CSV files** with the following names and columns:

### 1. `Courses`
| Column | Description |
|---------|--------------|
| CourseID | Unique course code |
| CourseName | Full course title |
| Credits | Number of credit hours |
| Type | Lab or Lecture |

### 2. `Instructors`
| Column | Description |
|---------|--------------|
| InstructorID | Unique instructor ID |
| Name | Instructor name |
| PreferredSlots | Notes like "Not on Sunday" |
| QualifiedCourses | Comma-separated list of course IDs |

### 3. `Rooms`
| Column | Description |
|---------|--------------|
| RoomID | Unique ID (e.g., Room101) |
| Type | Classroom or Lab |
| Capacity | Number of students it can hold |

### 4. `Sections`
| Column | Description |
|---------|--------------|
| SectionID | Unique section name (e.g., CS1) |
| StudentCount | Number of students in the section |
| Courses | Comma-separated list of course IDs |

### 5. `TimeSlots`
| Column | Description |
|---------|--------------|
| TimeSlotID | Unique ID for the slot |
| Day | Day of the week |
| StartTime | e.g., 08:00 AM |
| EndTime | e.g., 08:45 AM |

---

## 🧩 How It Works

1. **Data Loading**
   - The program reads all data from Excel or CSV using the `DataManager` class.
   - Each row is converted into Python objects (e.g., `Course`, `Instructor`, `Room`).

2. **Domain Creation**
   - For every `(Section, Course)` pair, possible combinations of `(TimeSlot, Room, Instructor)` are generated.
   - Invalid combinations (e.g., unavailable instructor or wrong room type) are excluded.

3. **Backtracking Search**
   - The `FinalFixSolver` assigns each variable using **MRV heuristic** (Minimum Remaining Values).
   - At each step, it checks for **consistency** (no conflicts).
   - If a conflict appears, the solver **backtracks** and tries another option.

4. **Constraint Checking**
   - Hard constraints: Instructor, Room, and Section cannot overlap.
   - Soft constraints: Avoid very early/late classes, overloaded days, etc.

5. **Performance Evaluation**
   - After generating a timetable, the `PerformanceTracker` counts:
     - Hard and soft constraint violations
     - Success rate
     - Generation time

6. **Results Export**
   - Final schedule is printed, saved as CSV, or stored in a database.

---

## 🧮 Core Components

| Component | Description |
|------------|-------------|
| **`Timetable`** | Stores all assignments and tracks conflicts |
| **`DataManager`** | Loads data from Excel/CSV and exports to DB |
| **`PerformanceTracker`** | Evaluates timetable quality |
| **`TimetableUI`** | Command-line user interface |
| **`FinalFixSolver`** | Main CSP solver using backtracking |
| **`load_data()`** | Helper for reading CSVs |
| **`print_timetable()`** | Prints results in readable format |
| **`export_to_csv()`** | Saves generated timetable to file |

---

## 🧰 Installation & Setup

### **1. Prerequisites**
- Python 3.9+
- Required libraries:
  ```bash
  pip install pandas numpy openpyxl

## Usage

```bash
python timetable_solver.py
```

🎛️  TIMETABLE GENERATOR
==========================================
    1. Generate Timetable from CSV
    2. Generate Timetable from Excel
    3. Show Current Timetable
    4. Show Performance Report
    5. Export to CSV
    6. Export to Database
    7. Exit

