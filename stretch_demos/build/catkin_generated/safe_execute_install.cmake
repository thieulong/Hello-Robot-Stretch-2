execute_process(COMMAND "/home/hello-robot/catkin_ws/src/stretch_ros/stretch_demos/build/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/hello-robot/catkin_ws/src/stretch_ros/stretch_demos/build/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
