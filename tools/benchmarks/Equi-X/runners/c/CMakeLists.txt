# Equi-X C benchmark runner.
#
# Builds the vendored tevador/equix + hashx static libraries (via add_subdirectory)
# and links them into `equix_runner`. blake2.c symbols come from hashx_static.
cmake_minimum_required(VERSION 3.10)
project(equix_runner C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
  message(STATUS "Setting default build type: ${CMAKE_BUILD_TYPE}")
endif()

# Location of the vendored equix source tree (contains hashx/ submodule).
if(NOT DEFINED EQUIX_DIR)
  set(EQUIX_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../vendored/equix")
endif()
get_filename_component(EQUIX_DIR "${EQUIX_DIR}" ABSOLUTE)

if(NOT EXISTS "${EQUIX_DIR}/include/equix.h")
  message(FATAL_ERROR "equix source not found at ${EQUIX_DIR}. Run scripts/setup.sh first.")
endif()

# The vendored equix/hashx use cmake_minimum_required(VERSION 2.8.8). CMake >= 4
# removes compatibility with < 3.5 (hard error) and deprecation-warns for < 3.10.
# Pin the policy floor to 3.10 so those submodules configure cleanly with neither
# the error nor the "Compatibility with CMake < 3.10 will be removed" warning.
if(NOT DEFINED CMAKE_POLICY_VERSION_MINIMUM)
  set(CMAKE_POLICY_VERSION_MINIMUM 3.10 CACHE STRING "" FORCE)
endif()

add_subdirectory("${EQUIX_DIR}" "${CMAKE_BINARY_DIR}/equix_ext")

add_executable(equix_runner
  equix_runner.c
  effort.c
  json_min.c
  sha256.c)

target_compile_definitions(equix_runner PRIVATE HASHX_SIZE=8 EQUIX_STATIC HASHX_STATIC)

target_include_directories(equix_runner PRIVATE
  "${EQUIX_DIR}/include"
  "${EQUIX_DIR}/hashx/include"
  "${EQUIX_DIR}/hashx/src")   # for the internal blake2.h

target_link_libraries(equix_runner PRIVATE equix_static hashx_static)

# Optional build-time provenance (set by scripts/setup.sh).
if(DEFINED EQUIX_C_COMMIT)
  target_compile_definitions(equix_runner PRIVATE EQUIX_C_COMMIT="${EQUIX_C_COMMIT}")
endif()
if(DEFINED EQUIX_C_VERSION)
  target_compile_definitions(equix_runner PRIVATE EQUIX_C_VERSION="${EQUIX_C_VERSION}")
endif()
