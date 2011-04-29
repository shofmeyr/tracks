from course import Course

class Courses:
    data = {}

    def load(cls, fname):
        f = open(fname, "r")
        for line in f.readlines():
            if line.strip() == "": continue
            if line.lstrip()[0] == "#": continue
            course = Course.fromString(line)
            if course.id in Courses.data:
                print "Duplicate course", course.id, "skipping..."
                continue
            Courses.data[course.id] = course
        f.close()
    load = classmethod(load)

    

