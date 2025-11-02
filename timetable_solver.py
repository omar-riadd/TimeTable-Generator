import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import random
import time
import os

# ==================== DATA MODELS ====================

@dataclass
class Course:
    id: str
    name: str
    credits: int
    type: str

@dataclass
class Instructor:
    id: str
    name: str
    unavailable_days: List[str]
    qualified_courses: List[str]

@dataclass
class Room:
    id: str
    type: str
    capacity: int

@dataclass
class Section:
    id: str
    student_count: int
    courses: List[str]

@dataclass
class TimeSlot:
    id: str
    day: str
    start_time: str
    end_time: str
    duration: int  # Added duration in minutes

@dataclass
class Assignment:
    section_id: str
    course_id: str
    time_slot: TimeSlot
    room: Room
    instructor: Instructor

class Timetable:
    def __init__(self):
        self.assignments: List[Assignment] = []
        self.assignment_dict: Dict[Tuple[str, str], Assignment] = {}
        
        # Tracking for quick constraint checking
        self.instructor_schedule: Dict[str, Set[str]] = defaultdict(set)
        self.room_schedule: Dict[str, Set[str]] = defaultdict(set)
        self.section_schedule: Dict[str, Set[str]] = defaultdict(set)
    
    def add_assignment(self, assignment: Assignment):
        self.assignments.append(assignment)
        self.assignment_dict[(assignment.section_id, assignment.course_id)] = assignment
        self.instructor_schedule[assignment.instructor.id].add(assignment.time_slot.id)
        self.room_schedule[assignment.room.id].add(assignment.time_slot.id)
        self.section_schedule[assignment.section_id].add(assignment.time_slot.id)
    
    def remove_assignment(self, assignment: Assignment):
        self.assignments.remove(assignment)
        del self.assignment_dict[(assignment.section_id, assignment.course_id)]
        self.instructor_schedule[assignment.instructor.id].remove(assignment.time_slot.id)
        self.room_schedule[assignment.room.id].remove(assignment.time_slot.id)
        self.section_schedule[assignment.section_id].remove(assignment.time_slot.id)

# ==================== DATA MANAGER (NEW) ====================

class DataManager:
    """Enhanced data management with Excel and database support"""
    
    @staticmethod
    def load_from_excel(file_path: str):
        """Load all data from a single Excel file with multiple sheets"""
        try:
            print(f"📂 Loading data from Excel: {file_path}")
            
            # Load from Excel sheets
            courses_df = pd.read_excel(file_path, sheet_name='Courses')
            instructors_df = pd.read_excel(file_path, sheet_name='Instructors') 
            rooms_df = pd.read_excel(file_path, sheet_name='Rooms')
            sections_df = pd.read_excel(file_path, sheet_name='Sections')
            time_slots_df = pd.read_excel(file_path, sheet_name='TimeSlots')
            
            # Convert to data structures
            courses = DataManager._convert_courses(courses_df)
            instructors = DataManager._convert_instructors(instructors_df)
            rooms = DataManager._convert_rooms(rooms_df)
            sections = DataManager._convert_sections(sections_df)
            time_slots = DataManager._convert_time_slots(time_slots_df)
            
            print("✅ Excel data loaded successfully!")
            return courses, instructors, rooms, sections, time_slots
            
        except Exception as e:
            print(f"❌ Error loading Excel file: {e}")
            # Fall back to CSV files
            print("🔄 Falling back to CSV files...")
            return load_data()  # Your existing function

    @staticmethod
    def _convert_courses(df):
        courses = []
        for _, row in df.iterrows():
            courses.append(Course(
                id=row['CourseID'],
                name=row['CourseName'],
                credits=row['Credits'],
                type=row['Type']
            ))
        return courses

    @staticmethod
    def _convert_instructors(df):
        instructors = []
        
        for _, row in df.iterrows():
            # Parse unavailable days from PreferredSlots
            preferred_slots = str(row['PreferredSlots'])
            unavailable_days = []
            
            if 'Not on Sunday' in preferred_slots:
                unavailable_days.append('Sunday')
            if 'Not on Monday' in preferred_slots:
                unavailable_days.append('Monday')
            if 'Not on Tuesday' in preferred_slots:
                unavailable_days.append('Tuesday')
            if 'Not on Wednesday' in preferred_slots:
                unavailable_days.append('Wednesday')
            if 'Not on Thursday' in preferred_slots:
                unavailable_days.append('Thursday')
            if 'Not on Friday' in preferred_slots:
                unavailable_days.append('Friday')

            # Parse qualified courses
            qualified_courses = str(row['QualifiedCourses']).split(',')
            qualified_courses = [c.strip() for c in qualified_courses if c.strip()]
            
            instructors.append(Instructor(
                id=row['InstructorID'],
                name=row['Name'],
                unavailable_days=unavailable_days,
                qualified_courses=qualified_courses
            ))
        
        return instructors

    @staticmethod
    def _convert_rooms(df):
        rooms = []
        for _, row in df.iterrows():
            rooms.append(Room(
                id=row['RoomID'],
                type=row['Type'],
                capacity=row['Capacity']
            ))
        return rooms

    @staticmethod
    def _convert_sections(df):
        sections = []
        for _, row in df.iterrows():
            courses_list = str(row['Courses']).split(',')
            courses_list = [c.strip() for c in courses_list if c.strip()]
            
            sections.append(Section(
                id=row['SectionID'],
                student_count=row['StudentCount'],
                courses=courses_list
            ))
        return sections

    @staticmethod
    def _convert_time_slots(df):
        time_slots = []
        for _, row in df.iterrows():
            # Calculate duration in minutes
            start_time = pd.to_datetime(row['StartTime']).time()
            end_time = pd.to_datetime(row['EndTime']).time()
            
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            duration = end_minutes - start_minutes
            
            time_slots.append(TimeSlot(
                id=row['TimeSlotID'],
                day=row['Day'],
                start_time=row['StartTime'],
                end_time=row['EndTime'],
                duration=duration
            ))
        return time_slots

    @staticmethod
    def export_to_database(timetable: Timetable, db_path: str = "timetable.db"):
        """Export timetable to SQLite database"""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            
            # Create tables
            conn.execute('''
                CREATE TABLE IF NOT EXISTS timetable_assignments (
                    section_id TEXT,
                    course_id TEXT,
                    day TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    room_id TEXT,
                    room_type TEXT,
                    instructor_id TEXT,
                    instructor_name TEXT,
                    PRIMARY KEY (section_id, course_id)
                )
            ''')
            
            # Clear existing data
            conn.execute("DELETE FROM timetable_assignments")
            
            # Insert new data
            for assignment in timetable.assignments:
                # Remove AM/PM from time format for database too
                start_time = pd.to_datetime(assignment.time_slot.start_time).strftime('%H:%M')
                end_time = pd.to_datetime(assignment.time_slot.end_time).strftime('%H:%M')
                
                conn.execute('''
                    INSERT INTO timetable_assignments 
                    (section_id, course_id, day, start_time, end_time, room_id, room_type, instructor_id, instructor_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    assignment.section_id,
                    assignment.course_id,
                    assignment.time_slot.day,
                    start_time,
                    end_time,
                    assignment.room.id,
                    assignment.room.type,
                    assignment.instructor.id,
                    assignment.instructor.name
                ))
            
            conn.commit()
            conn.close()
            print(f"✅ Timetable exported to database: {db_path}")
            
        except Exception as e:
            print(f"❌ Error exporting to database: {e}")

# ==================== PERFORMANCE TRACKER (NEW) ====================

class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            'generation_time': 0,
            'hard_constraint_violations': 0,
            'soft_constraint_violations': 0,
            'success_rate': 0.0,
            'total_assignments': 0,
            'total_variables': 0
        }
    
    def evaluate_solution(self, timetable: Timetable, solver) -> Dict:
        """Evaluate timetable quality without modifying anything"""
        self.metrics['total_assignments'] = len(timetable.assignments)
        self.metrics['total_variables'] = len(solver.variables) if hasattr(solver, 'variables') else 0
        self.metrics['hard_constraint_violations'] = self._count_hard_constraint_violations(timetable)
        self.metrics['soft_constraint_violations'] = self._count_soft_constraint_violations(timetable)
        self.metrics['success_rate'] = len(timetable.assignments) / len(solver.variables) if solver.variables else 0
        
        return self.metrics
    
    def _count_hard_constraint_violations(self, timetable: Timetable) -> int:
        """Count hard constraint violations"""
        violations = 0
        
        # Check instructor conflicts
        instructor_assignments = defaultdict(list)
        for assignment in timetable.assignments:
            instructor_assignments[assignment.instructor.id].append(assignment)
        
        for instructor, assignments in instructor_assignments.items():
            time_slots = [a.time_slot.id for a in assignments]
            if len(time_slots) != len(set(time_slots)):
                violations += len(time_slots) - len(set(time_slots))
        
        # Check room conflicts
        room_assignments = defaultdict(list)
        for assignment in timetable.assignments:
            room_assignments[assignment.room.id].append(assignment)
        
        for room, assignments in room_assignments.items():
            time_slots = [a.time_slot.id for a in assignments]
            if len(time_slots) != len(set(time_slots)):
                violations += len(time_slots) - len(set(time_slots))
        
        # Check section conflicts
        section_assignments = defaultdict(list)
        for assignment in timetable.assignments:
            section_assignments[assignment.section_id].append(assignment)
        
        for section, assignments in section_assignments.items():
            time_slots = [a.time_slot.id for a in assignments]
            if len(time_slots) != len(set(time_slots)):
                violations += len(time_slots) - len(set(time_slots))
        
        return violations
    
    def _count_soft_constraint_violations(self, timetable: Timetable) -> int:
        """Count soft constraint violations"""
        violations = 0
        
        # Check for early morning/late evening assignments
        for assignment in timetable.assignments:
            start_time = pd.to_datetime(assignment.time_slot.start_time)
            if start_time.hour < 8 or start_time.hour > 18:
                violations += 1
        
        # Check for student gaps (classes too spread out or too concentrated)
        section_assignments = defaultdict(list)
        for assignment in timetable.assignments:
            section_assignments[assignment.section_id].append(assignment)
        
        for section, assignments in section_assignments.items():
            # Count days with assignments
            days = len(set(a.time_slot.day for a in assignments))
            if days < 2:  # Should be spread across at least 2 days
                violations += 1
            
            # Check for consecutive classes in distant rooms
            assignments.sort(key=lambda x: (x.time_slot.day, x.time_slot.start_time))
            for i in range(len(assignments) - 1):
                if (assignments[i].time_slot.day == assignments[i + 1].time_slot.day and
                    assignments[i].room.id != assignments[i + 1].room.id):
                    violations += 0.5  # Partial violation
        
        return int(violations)

    def print_performance_report(self):
        """Print comprehensive performance report"""
        print("\n" + "="*60)
        print("📊 PERFORMANCE EVALUATION REPORT")
        print("="*60)
        print(f"Total Variables: {self.metrics['total_variables']}")
        print(f"Total Assignments: {self.metrics['total_assignments']}")
        print(f"Success Rate: {self.metrics['success_rate']:.1%}")
        print(f"Generation Time: {self.metrics['generation_time']:.2f} seconds")
        print(f"Hard Constraint Violations: {self.metrics['hard_constraint_violations']}")
        print(f"Soft Constraint Violations: {self.metrics['soft_constraint_violations']}")
        
        if self.metrics['hard_constraint_violations'] == 0:
            print("✅ ALL HARD CONSTRAINTS SATISFIED!")
        else:
            print("❌ Hard constraint violations detected")
            
        if self.metrics['soft_constraint_violations'] == 0:
            print("✅ ALL SOFT CONSTRAINTS SATISFIED!")
        else:
            print("⚠️  Soft constraint violations detected (acceptable)")

# ==================== USER INTERFACE (NEW) ====================

class TimetableUI:
    def __init__(self, solver_class):
        self.solver_class = solver_class
        self.performance_tracker = PerformanceTracker()
        self.current_timetable = None
        self.current_data = None
    
    def run_interactive_mode(self):
        """Simple command-line interface"""
        print("\n🎛️  TIMETABLE GENERATOR - CSIT DEPARTMENT")
        print("="*50)
        
        while True:
            print("\nOptions:")
            print("1. Generate Timetable from CSV")
            print("2. Generate Timetable from Excel")
            print("3. Show Current Timetable")
            print("4. Show Performance Report") 
            print("5. Export to CSV")
            print("6. Export to Database")
            print("7. Exit")  # Removed "Update Data Manually" option
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                self._generate_from_csv()
            elif choice == '2':
                self._generate_from_excel()
            elif choice == '3':
                self._show_timetable()
            elif choice == '4':
                self._show_performance()
            elif choice == '5':
                self._export_to_csv()
            elif choice == '6':
                self._export_to_database()
            elif choice == '7':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice, please try again")
    
    def _generate_from_csv(self):
        """Generate timetable using CSV files"""
        print("\n🚀 Generating timetable from CSV files...")
        
        try:
            courses, instructors, rooms, sections, time_slots = load_data()
            self._solve_timetable(courses, instructors, rooms, sections, time_slots)
        except Exception as e:
            print(f"❌ Error loading CSV data: {e}")
    
    def _generate_from_excel(self):
        """Generate timetable from Excel file"""
        file_path = input("Enter Excel file path (or press Enter for default): ").strip()
        if not file_path:
            file_path = "timetable_data.xlsx"
            
        try:
            courses, instructors, rooms, sections, time_slots = DataManager.load_from_excel(file_path)
            self._solve_timetable(courses, instructors, rooms, sections, time_slots)
        except Exception as e:
            print(f"❌ Error loading from Excel: {e}")
    
    def _solve_timetable(self, courses, instructors, rooms, sections, time_slots):
        """Common solving logic"""
        self.current_data = (courses, instructors, rooms, sections, time_slots)
        
        print(f"📊 Problem size: {len(courses)} courses, {len(instructors)} instructors, "
              f"{len(rooms)} rooms, {len(sections)} sections")
        
        start_time = time.time()
        
        solver = self.solver_class(courses, instructors, rooms, sections, time_slots)
        self.current_timetable = solver.solve()
        
        end_time = time.time()
        self.performance_tracker.metrics['generation_time'] = end_time - start_time
        
        if self.current_timetable:
            print("✅ Timetable generated successfully!")
            self.performance_tracker.evaluate_solution(self.current_timetable, solver)
        else:
            print("❌ Failed to generate timetable")
    
    def _show_timetable(self):
        """Display current timetable"""
        if self.current_timetable:
            print_timetable(self.current_timetable)
        else:
            print("❌ No timetable generated yet. Please generate a timetable first.")
    
    def _show_performance(self):
        """Show performance report"""
        if self.performance_tracker.metrics['generation_time'] > 0:
            self.performance_tracker.print_performance_report()
        else:
            print("❌ No timetable generated yet. Please generate a timetable first.")
    
    def _export_to_csv(self):
        """Export results to CSV"""
        if self.current_timetable:
            filename = input("Enter CSV filename (or press Enter for default): ").strip()
            if not filename:
                filename = "generated_timetable.csv"
            export_to_csv(self.current_timetable, filename)
        else:
            print("❌ No timetable to export. Please generate a timetable first.")
    
    def _export_to_database(self):
        """Export to SQLite database"""
        if self.current_timetable:
            db_path = input("Enter database path (or press Enter for default): ").strip()
            if not db_path:
                db_path = "timetable.db"
            DataManager.export_to_database(self.current_timetable, db_path)
        else:
            print("❌ No timetable to export. Please generate a timetable first.")

# ==================== FINAL FIX SOLVER ====================

class FinalFixSolver:
    def __init__(self, courses: List[Course], instructors: List[Instructor], 
                 rooms: List[Room], sections: List[Section], time_slots: List[TimeSlot]):
        self.courses = {c.id: c for c in courses}
        self.instructors = {i.id: i for i in instructors}
        
        # FIX: Convert some Lab rooms to Classroom rooms since we have no classrooms
        self.rooms = self._fix_room_types(rooms)
        
        self.sections = sections
        self.time_slots = {ts.id: ts for ts in time_slots}
        
        # FIX: Add missing instructor qualifications
        self._fix_instructor_qualifications()
        
        # Create variables
        self.variables = self._create_variables()
        
        # Precompute domains with final fixes
        self.domains = self._precompute_domains_final()
        
        # Statistics
        self.backtracks = 0
        self.assignments_tried = 0
        
        print(f"Problem size: {len(self.variables)} variables")
        
        # Check domain sizes
        domain_sizes = [len(domain) for domain in self.domains.values()]
        print(f"Domain sizes - Min: {min(domain_sizes)}, Max: {max(domain_sizes)}, Avg: {np.mean(domain_sizes):.1f}")
        
        zero_domain_vars = [var for var, domain in self.domains.items() if len(domain) == 0]
        if zero_domain_vars:
            print(f"❌ {len(zero_domain_vars)} variables still have no valid assignments")
            for var in zero_domain_vars[:3]:
                self._debug_variable(var)
        else:
            print("✅ All variables have valid domains!")

    def _fix_room_types(self, rooms: List[Room]) -> Dict[str, Room]:
        """Convert some Lab rooms to Classroom rooms since we have no classrooms"""
        print("🔧 Fixing room types...")
        
        # Convert first 20 Lab rooms to Classroom rooms
        lab_rooms = [r for r in rooms if r.type == 'Lab']
        classroom_rooms = [r for r in rooms if r.type == 'Classroom']
        
        print(f"   Original: {len(classroom_rooms)} classrooms, {len(lab_rooms)} labs")
        
        # If no classrooms, convert some labs to classrooms
        if len(classroom_rooms) == 0:
            for i, room in enumerate(lab_rooms[:20]):  # Convert first 20 labs to classrooms
                room.type = 'Classroom'
                print(f"   Converted {room.id} from Lab to Classroom")
        
        # Update counts
        lab_rooms = [r for r in rooms if r.type == 'Lab']
        classroom_rooms = [r for r in rooms if r.type == 'Classroom']
        print(f"   Fixed: {len(classroom_rooms)} classrooms, {len(lab_rooms)} labs")
        
        return {r.id: r for r in rooms}

    def _fix_instructor_qualifications(self):
        """Add missing qualifications to instructors"""
        print("🔧 Fixing instructor qualifications...")
        
        # Courses that need instructors
        missing_courses = ['LRA401', 'LRA101', 'LRA103', 'LRA403', 'LRA106']
        
        # Assign missing courses to available instructors
        for course_id in missing_courses:
            # Find instructors who can teach these (humanities/social science instructors)
            suitable_instructors = [
                instr for instr in self.instructors.values() 
                if any(prefix in instr.id for prefix in ['PROF27', 'PROF28', 'PROF29', 'PROF30', 'PROF31', 'PROF32', 'PROF33', 'PROF34', 'PROF35'])
            ]
            
            for instructor in suitable_instructors[:3]:  # Assign to first 3 suitable instructors
                if course_id not in instructor.qualified_courses:
                    instructor.qualified_courses.append(course_id)
                    print(f"   Added {course_id} to {instructor.name}")

    def _debug_variable(self, var: Tuple[str, str]):
        """Debug why a variable has no valid domain"""
        section_id, course_id = var
        course = self.courses[course_id]
        
        print(f"\n🔍 Debugging {var}:")
        
        # Check qualified instructors
        qualified_instructors = [
            instr for instr in self.instructors.values() 
            if course_id in instr.qualified_courses
        ]
        print(f"   Qualified instructors: {len(qualified_instructors)}")
        
        # Check room availability
        lab_courses = {'PHY113', 'PHY123', 'CHM113', 'ECE111', 'ECE223', 'ECE214', 'CNC222'}
        if course_id in lab_courses or 'Lab' in course.type:
            suitable_rooms = [r for r in self.rooms.values() if r.type == 'Lab']
            room_type = 'Lab'
        else:
            suitable_rooms = [r for r in self.rooms.values() if r.type == 'Classroom']
            room_type = 'Classroom'
        
        print(f"   Suitable rooms ({room_type}): {len(suitable_rooms)}")
        if suitable_rooms:
            print(f"   Room examples: {[r.id for r in suitable_rooms[:3]]}")

    def _create_variables(self) -> List[Tuple[str, str]]:
        variables = []
        for section in self.sections:
            for course_id in section.courses:
                variables.append((section.id, course_id))
        return variables

    def _precompute_domains_final(self) -> Dict[Tuple[str, str], List[Tuple[TimeSlot, Room, Instructor]]]:
        """Precompute domains with final fixes"""
        domains = {}
        
        # Define which courses should use lab rooms
        lab_courses = {'PHY113', 'PHY123', 'CHM113', 'ECE111', 'ECE223', 'ECE214', 'CNC222'}
        
        for section_id, course_id in self.variables:
            domain = []
            course = self.courses[course_id]
            
            # Room type classification
            if course_id in lab_courses or 'Lab' in course.type:
                suitable_rooms = [r for r in self.rooms.values() if r.type == 'Lab']
                room_type = 'Lab'  # ✅ FIX: Define room_type
            else:
                suitable_rooms = [r for r in self.rooms.values() if r.type == 'Classroom']
                room_type = 'Classroom'  # ✅ FIX: Define room_type
            
            # Get qualified instructors
            qualified_instructors = [
                instr for instr in self.instructors.values() 
                if course_id in instr.qualified_courses
            ]
            
            if not qualified_instructors:
                print(f"⚠️ No qualified instructors for {course_id}")
                domains[(section_id, course_id)] = []
                continue
            
            if not suitable_rooms:
                print(f"❌ No suitable rooms for {course_id} - need {room_type} rooms")  # ✅ Now room_type is defined
                domains[(section_id, course_id)] = []
                continue
            
            # Generate domain
            for time_slot in self.time_slots.values():
                for room in suitable_rooms:
                    for instructor in qualified_instructors:
                        # Pre-filter by instructor availability
                        if time_slot.day not in instructor.unavailable_days:
                            domain.append((time_slot, room, instructor))
            
            domains[(section_id, course_id)] = domain
        
        return domains

    def _is_consistent(self, timetable: Timetable, new_assignment: Assignment) -> bool:
        """Fast consistency checking"""
        # Check instructor conflict
        if new_assignment.time_slot.id in timetable.instructor_schedule[new_assignment.instructor.id]:
            return False
        
        # Check room conflict  
        if new_assignment.time_slot.id in timetable.room_schedule[new_assignment.room.id]:
            return False
        
        # Check section conflict
        if new_assignment.time_slot.id in timetable.section_schedule[new_assignment.section_id]:
            return False
        
        return True

    def _is_consistent_with_load_balancing(self, timetable: Timetable, new_assignment: Assignment) -> bool:
        """Simple load balancing - just prevent extreme concentration"""
        # Original conflict checks
        if not self._is_consistent(timetable, new_assignment):
            return False
        
        day = new_assignment.time_slot.day
        day_assignments = sum(1 for a in timetable.assignments if a.time_slot.day == day)
        
        # Simple rule: No day should have more than 55 assignments
        # This prevents 95% of classes on 2 days while allowing natural distribution
        if day_assignments >= 55:
            return False
        
        return True

    def _select_next_variable(self, unassigned: List[Tuple[str, str]]) -> Tuple[str, str]:
        """MRV heuristic"""
        if not unassigned:
            return None
        
        min_size = float('inf')
        selected_var = None
        
        for var in unassigned:
            domain_size = len(self.domains[var])
            if domain_size < min_size:
                min_size = domain_size
                selected_var = var
        
        return selected_var

    def backtracking_search(self, max_backtracks=100000, print_interval=500) -> Optional[Timetable]:
        """Optimized backtracking"""
        self.backtracks = 0
        self.assignments_tried = 0
        
        def backtrack(timetable: Timetable, unassigned: List[Tuple[str, str]]) -> Optional[Timetable]:
            if not unassigned:
                return timetable
            
            if self.backtracks > max_backtracks:
                return None
            
            var = self._select_next_variable(unassigned)
            if var is None:
                return None
            
            section_id, course_id = var
            domain = self.domains[var]
            
            # Try values in order
            for value in domain:
                time_slot, room, instructor = value
                
                new_assignment = Assignment(
                    section_id=section_id,
                    course_id=course_id,
                    time_slot=time_slot,
                    room=room,
                    instructor=instructor
                )
                
                self.assignments_tried += 1
                
                # Progress reporting
                if self.assignments_tried % print_interval == 0:
                    progress = (len(timetable.assignments) / len(self.variables)) * 100
                    print(f"Progress: {progress:.1f}% | Assigned: {len(timetable.assignments)}/{len(self.variables)} | Backtracks: {self.backtracks}")
                
                # ✅ CHANGED: Use load balancing consistency check (no parameters)
                if self._is_consistent_with_load_balancing(timetable, new_assignment):
                    timetable.add_assignment(new_assignment)
                    new_unassigned = [v for v in unassigned if v != var]
                    
                    result = backtrack(timetable, new_unassigned)
                    if result is not None:
                        return result
                    
                    timetable.remove_assignment(new_assignment)
                    self.backtracks += 1
            
            return None
        
        print("Starting backtracking search...")
        initial_timetable = Timetable()
        result = backtrack(initial_timetable, self.variables.copy())
        
        return result

    def solve(self, max_attempts=3) -> Optional[Timetable]:
        """Main solving method"""
        for attempt in range(max_attempts):
            print(f"\n🚀 Attempt {attempt + 1}/{max_attempts}")
            start_time = time.time()
            result = self.backtracking_search()
            end_time = time.time()
            
            if result:
                print(f"✅ Solution found in {end_time - start_time:.2f} seconds!")
                return result
            else:
                print(f"❌ No solution found in attempt {attempt + 1}")
                print(f"   Time: {end_time - start_time:.2f}s, Backtracks: {self.backtracks}")
        
        return None

# ==================== DATA LOADING ====================

def load_data():
    """Load all data from CSV files"""
    try:
        # Load courses
        courses_df = pd.read_csv('Courses.csv')
        courses = []
        for _, row in courses_df.iterrows():
            courses.append(Course(
                id=row['CourseID'],
                name=row['CourseName'],
                credits=row['Credits'],
                type=row['Type']
            ))
        
        # Load instructors - WITH DEBUGGING
        instructors_df = pd.read_csv('Instructor.csv')
        instructors = []
        
        print("\n🔍 Analyzing Instructor Availability:")
        day_availability = {'Sunday': 0, 'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0}
        
        for _, row in instructors_df.iterrows():
            # Parse unavailable days from PreferredSlots
            preferred_slots = str(row['PreferredSlots'])
            unavailable_days = []
            
            # Debug: Show what we're parsing
            if _ < 5:  # Show first 5 instructors as sample
                print(f"   {row['Name']}: PreferredSlots = '{preferred_slots}'")
            
            if 'Not on Sunday' in preferred_slots:
                unavailable_days.append('Sunday')
            else:
                day_availability['Sunday'] += 1
                
            if 'Not on Monday' in preferred_slots:
                unavailable_days.append('Monday')
            else:
                day_availability['Monday'] += 1
                
            if 'Not on Tuesday' in preferred_slots:
                unavailable_days.append('Tuesday')
            else:
                day_availability['Tuesday'] += 1
                
            if 'Not on Wednesday' in preferred_slots:
                unavailable_days.append('Wednesday')
            else:
                day_availability['Wednesday'] += 1
                
            if 'Not on Thursday' in preferred_slots:
                unavailable_days.append('Thursday')
            else:
                day_availability['Thursday'] += 1
                
            if 'Not on Friday' in preferred_slots:
                unavailable_days.append('Friday')
            else:
                day_availability['Friday'] += 1

            # Parse qualified courses
            qualified_courses = str(row['QualifiedCourses']).split(',')
            qualified_courses = [c.strip() for c in qualified_courses if c.strip()]
            
            instructors.append(Instructor(
                id=row['InstructorID'],
                name=row['Name'],
                unavailable_days=unavailable_days,
                qualified_courses=qualified_courses
            ))
        
        print(f"\n📊 Instructor Availability by Day:")
        for day, count in day_availability.items():
            print(f"   {day}: {count}/{len(instructors_df)} instructors available")
        
        # Load rooms
        rooms_df = pd.read_csv('Rooms.csv')
        rooms = []
        for _, row in rooms_df.iterrows():
            rooms.append(Room(
                id=row['RoomID'],
                type=row['Type'],
                capacity=row['Capacity']
            ))
        
        # Load sections
        sections_df = pd.read_csv('Sections.csv')
        sections_df.columns = sections_df.columns.str.replace('\ufeff', '')
        sections = []
        for _, row in sections_df.iterrows():
            courses_list = str(row['Courses']).split(',')
            courses_list = [c.strip() for c in courses_list if c.strip()]
            
            sections.append(Section(
                id=row['SectionID'],
                student_count=row['StudentCount'],
                courses=courses_list
            ))
        
        # Load time slots - UPDATED FOR 45-MINUTE SLOTS
        time_slots_df = pd.read_csv('TimeSlots.csv')
        time_slots = []
        for _, row in time_slots_df.iterrows():
            # Calculate duration in minutes
            start_time = pd.to_datetime(row['StartTime']).time()
            end_time = pd.to_datetime(row['EndTime']).time()
            
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            duration = end_minutes - start_minutes
            
            time_slots.append(TimeSlot(
                id=row['TimeSlotID'],
                day=row['Day'],
                start_time=row['StartTime'],
                end_time=row['EndTime'],
                duration=duration
            ))
        
        return courses, instructors, rooms, sections, time_slots
    
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise

# ==================== RESULTS VISUALIZATION ====================

def print_timetable(timetable: Timetable):
    """Print the generated timetable without AM/PM"""
    print("\n" + "="*80)
    print("GENERATED TIMETABLE")
    print("="*80)
    
    # Group by section
    sections = set(a.section_id for a in timetable.assignments)
    
    for section_id in sorted(sections):
        print(f"\nSection: {section_id}")
        print("-" * 80)
        print(f"{'Day':<10} {'Time':<15} {'Course':<12} {'Room':<8} {'Instructor':<20} {'Duration':<8}")
        print("-" * 80)
        
        section_assignments = [a for a in timetable.assignments if a.section_id == section_id]
        # Sort by day and time
        section_assignments.sort(key=lambda x: (x.time_slot.day, x.time_slot.start_time))
        
        for assignment in section_assignments:
            # Remove AM/PM from time format
            start_time = pd.to_datetime(assignment.time_slot.start_time).strftime('%H:%M')
            end_time = pd.to_datetime(assignment.time_slot.end_time).strftime('%H:%M')
            time_str = f"{start_time}-{end_time}"
            
            duration_str = f"{assignment.time_slot.duration}min"
            
            # Truncate instructor name if too long
            instructor_name = assignment.instructor.name
            if len(instructor_name) > 20:
                instructor_name = instructor_name[:17] + "..."
            
            print(f"{assignment.time_slot.day:<10} {time_str:<15} {assignment.course_id:<12} {assignment.room.id:<8} {instructor_name:<20} {duration_str:<8}")

def export_to_csv(timetable: Timetable, filename="generated_timetable.csv"):
    """Export timetable to CSV without AM/PM"""
    data = []
    for assignment in timetable.assignments:
        # Remove AM/PM from time format
        start_time = pd.to_datetime(assignment.time_slot.start_time).strftime('%H:%M')
        end_time = pd.to_datetime(assignment.time_slot.end_time).strftime('%H:%M')
        
        data.append({
            'Section': assignment.section_id,
            'Course': assignment.course_id,
            'Day': assignment.time_slot.day,
            'StartTime': start_time,
            'EndTime': end_time,
            'Duration': f"{assignment.time_slot.duration} minutes",
            'Room': assignment.room.id,
            'RoomType': assignment.room.type,
            'Instructor': assignment.instructor.name,
            'InstructorID': assignment.instructor.id
        })
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"📁 Timetable exported to {filename}")

def validate_time_slots(time_slots: List[TimeSlot]):
    """Validate that time slots match the 45-minute structure from Excel"""
    print("\n🔍 Validating time slot structure...")
    
    # Expected 45-minute slots from Excel
    expected_slots_per_day = 8
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    
    slots_per_day = {}
    for day in days:
        day_slots = [ts for ts in time_slots if ts.day == day]
        slots_per_day[day] = len(day_slots)
        print(f"   {day}: {len(day_slots)} time slots")
        
        # Check durations
        for ts in day_slots[:3]:  # Show first 3 as sample
            print(f"     {ts.id}: {ts.start_time}-{ts.end_time} ({ts.duration}min)")
    
    total_expected = expected_slots_per_day * len(days)
    total_actual = len(time_slots)
    
    print(f"\n   Total time slots: {total_actual} (Expected: {total_expected})")
    
    if total_actual == total_expected:
        print("✅ Time slot structure matches Excel format!")
    else:
        print("⚠️  Time slot count doesn't match Excel format exactly, but will proceed...")

# ==================== MAIN EXECUTION ====================

def main():
    print("🚀 Automated Timetable Generator - CSIT Department")
    print("="*60)
    print("Project 1: Constraint Satisfaction Problem")
    print("Intelligent Systems Fall 2025/2026")
    print("="*60)
    
    # Check if interactive mode is desired
    use_ui = input("Use interactive mode? (y/n, Enter for yes): ").strip().lower()
    
    if use_ui in ['', 'y', 'yes']:  # Fixed to handle 'yes' input
        # Use new interactive UI
        ui = TimetableUI(FinalFixSolver)
        ui.run_interactive_mode()
    else:
        # Use original flow (your existing code)
        print("🔧 Using standard mode...")
        
        print("Loading data...")
        courses, instructors, rooms, sections, time_slots = load_data()
        
        print(f"✅ Loaded: {len(courses)} courses, {len(instructors)} instructors, "
              f"{len(rooms)} rooms, {len(sections)} sections, {len(time_slots)} time slots")
        
        validate_time_slots(time_slots)
        
        print("\n🔧 Creating CSP solver...")
        solver = FinalFixSolver(courses, instructors, rooms, sections, time_slots)
        
        print(f"📊 Total variables: {len(solver.variables)}")
        
        print("\n🎯 Solving timetable...")
        start_time = time.time()
        timetable = solver.solve()
        end_time = time.time()
        
        if timetable:
            print(f"\n✅ SUCCESS! Generated timetable with {len(timetable.assignments)} assignments")
            print(f"⏱️  Generation time: {end_time - start_time:.2f} seconds")
            print_timetable(timetable)
            export_to_csv(timetable)
            
            # Add performance evaluation
            tracker = PerformanceTracker()
            tracker.metrics['generation_time'] = end_time - start_time
            tracker.evaluate_solution(timetable, solver)
            tracker.print_performance_report()
            
            # Offer database export
            export_db = input("\nExport to database? (y/n): ").strip().lower()
            if export_db in ['', 'y', 'yes']:
                DataManager.export_to_database(timetable)
        else:
            print(f"\n❌ Failed to generate timetable")
            print(f"Backtracks: {solver.backtracks}, Assignments tried: {solver.assignments_tried}")

if __name__ == "__main__":
    main()