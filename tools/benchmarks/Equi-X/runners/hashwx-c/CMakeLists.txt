# HashWX benchmark runner. Builds the pinned tevador/hashwx static library and
# links it into hashwx_runner and hashwx_vectors. scripts/setup_hashwx.sh fetches
# the source. Run that script rather than this file.
cmake_minimum_required(VERSION 3.10)
project(hashwx_runner C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

if(NOT DEFINED HASHWX_DIR)
  set(HASHWX_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../vendored/hashwx")
endif()
get_filename_component(HASHWX_DIR "${HASHWX_DIR}" ABSOLUTE)

if(NOT EXISTS "${HASHWX_DIR}/include/hashwx.h")
  message(FATAL_ERROR "hashwx source not found at ${HASHWX_DIR}. Run scripts/setup_hashwx.sh first.")
endif()

add_subdirectory("${HASHWX_DIR}" "${CMAKE_BINARY_DIR}/hashwx_ext")

set(SHARED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../c")

add_executable(hashwx_runner
  hashwx_runner.c
  blake2b.c
  "${SHARED_DIR}/json_min.c"
  "${SHARED_DIR}/sha256.c")
target_include_directories(hashwx_runner PRIVATE "${HASHWX_DIR}/include" "${SHARED_DIR}")
target_link_libraries(hashwx_runner PRIVATE hashwx_static)

add_executable(hashwx_vectors hashwx_vectors.c blake2b.c)
target_include_directories(hashwx_vectors PRIVATE "${HASHWX_DIR}/include")
target_link_libraries(hashwx_vectors PRIVATE hashwx_static)

if(DEFINED HASHWX_C_COMMIT)
  target_compile_definitions(hashwx_runner PRIVATE HASHWX_C_COMMIT="${HASHWX_C_COMMIT}")
endif()
if(DEFINED HASHWX_C_VERSION)
  target_compile_definitions(hashwx_runner PRIVATE HASHWX_C_VERSION="${HASHWX_C_VERSION}")
endif()
