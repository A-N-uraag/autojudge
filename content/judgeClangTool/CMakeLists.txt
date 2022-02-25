project(clangjudge)

cmake_minimum_required(VERSION 3.10)

#find_package(LLVM 10.0.0 REQUIRED)
find_package(LLVM 10.0.0 CONFIG REQUIRED)


set(Clang_DIR "/usr/lib/cmake/clang-10")

find_package(Clang REQUIRED CONFIG)

message(STATUS "LLVM found! ${LLVM_INSTALL_PREFIX}")
message(STATUS "Clang found! ${CLANG_INSTALL_PREFIX}")


file(GLOB checkers src/*.cpp)

add_executable(clangjudge
   ${checkers}
)

set(CLANG_LIBS

	  clangFrontend 
	  clangSerialization 
	  clangDriver 
	  clangParse 
	  clangSema 
	  clangAnalysis 
	  clangAST 
	  clangBasic 
	  clangEdit 
	  clangLex 
	  clangTooling

	)

target_include_directories(clangjudge PRIVATE ${CLANG_INCLUDE_DIRS})
target_link_libraries(clangjudge ${CLANG_LIBS} stdc++fs)
