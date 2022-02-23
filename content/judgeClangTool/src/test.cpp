#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Driver/Options.h"
#include "clang/Frontend/ASTConsumers.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"

#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/FileManager.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Basic/TargetInfo.h"
#include "clang/Basic/TargetOptions.h"

#include "clang/Parse/ParseAST.h"

#include "llvm/Support/Host.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/raw_ostream.h"

#include <bits/stdc++.h>
#include <string.h>
#include <experimental/filesystem>

using namespace clang;
using namespace clang::tooling;
using namespace llvm;

cl::opt<bool> AllChecks("all",cl::desc("Enables all checks"),cl::init(false));
cl::opt<bool> StringAllChecks("string-all-check",cl::desc("Enables all string checks"),cl::init(false));
cl::opt<bool> StrCmpCheck("strcmp-check",cl::desc("Enables strcmp  checks"),cl::init(false));
cl::opt<bool> StrCpyCheck("strcpy-check",cl::desc("Enables strcpy  checks"),cl::init(false));
cl::opt<bool> StrLenCheck("strlen-check",cl::desc("Enables strlen  checks"),cl::init(false));
cl::opt<bool> SystemAllChecks("sys-all-check",cl::desc("Enables all system checks"),cl::init(false));

enum FAILTYPE{
  NoFailure=0,
  StringFailType=20,
  SysFailType=30,
  FileFailType=40 
};

static FAILTYPE FAIL=NoFailure;

static const char *strFuncs[] = {
    "strlen", "strcat",  "strncat", "strcpy",  "strncpy", "strcmp",  "strncmp",
    "strchr", "strrchr", "strstr",  "strcspn", "strspn",  "strpbrk", "strtok"};

static const char *sysFuncs[] ={
    "syscall","system","fork","exec","wait","kill","rmdir"};

class UsedVar : public RecursiveASTVisitor<UsedVar> {

public:
  size_t strFunlength;
  size_t sysFunlength;
  explicit UsedVar(ASTContext *Context) : Context(Context) {
   
    strFunlength = sizeof(strFuncs) / sizeof(strFuncs[0]);
    sysFunlength = sizeof(sysFuncs) / sizeof(sysFuncs[0]);
  }

  void printMsg(Stmt *qst,std::string functionName,FAILTYPE fail) {
    
    FAIL=fail;  

    FullSourceLoc FullLocation = Context->getFullLoc(qst->getBeginLoc());
    if (FullLocation.isValid() && !FullLocation.isInSystemHeader())	    
      llvm::outs() << functionName <<" used at line number: "
                   << FullLocation.getSpellingLineNumber() << ":"
                   << FullLocation.getSpellingColumnNumber() << "\n";
  }

  bool VisitCallExpr(CallExpr *cl) {
    auto FuncDecl = cl->getDirectCallee();
    if(StringAllChecks){
     for (int i = 0; i < strFunlength; i++) {
	if (FuncDecl && FuncDecl->getNameInfo().getAsString() == strFuncs[i]) {
       	   if (Context->getSourceManager().isInSystemHeader(FuncDecl->getLocation())){
             llvm::outs() << FuncDecl->getNameInfo().getAsString() << "\n";
             printMsg(cl,strFuncs[i],StringFailType);
	   }
        }
      }
    }
    else if(StrCmpCheck){
      if (FuncDecl && FuncDecl->getNameInfo().getAsString() == "strcmp") {
         if (Context->getSourceManager().isInSystemHeader(FuncDecl->getLocation()))
             printMsg(cl,"strcmp",StringFailType);
      }
    }
    else if(StrLenCheck){
      if (FuncDecl && FuncDecl->getNameInfo().getAsString() == "strlen") {
         if (Context->getSourceManager().isInSystemHeader(FuncDecl->getLocation()))
             printMsg(cl,"strlen",StringFailType);
      }
    }
    else if(StrCpyCheck){
      if (FuncDecl && FuncDecl->getNameInfo().getAsString() == "strcpy") {
         if (Context->getSourceManager().isInSystemHeader(FuncDecl->getLocation()))
             printMsg(cl,"strcpy",StringFailType);
      }
    }
    if(FuncDecl && FuncDecl->getNameInfo().getAsString() == "fopen") {
    	
	clang::LangOptions LangOpts;
    	LangOpts.CPlusPlus = true;
    	clang::PrintingPolicy Policy(LangOpts);

	    
	     		
	std::string TypeS;
        llvm::raw_string_ostream s(TypeS);
        cl->getArg(0)->printPretty(s, 0, Policy);
 	
	std::string test=s.str();
	test.erase(remove( test.begin(), test.end(), '\"' ),test.end());
	
	std::experimental::filesystem::path p(test);

	//std::cout<<p.parent_path().string()<<"\n";

    	if (p.parent_path()!="inputs"){
          printMsg(cl,"wrong fopen",FileFailType);		
    	}
	
    } 
    if(SystemAllChecks){
     for (int i = 0; i < sysFunlength; i++) {
        if (FuncDecl && FuncDecl->getNameInfo().getAsString() == sysFuncs[i]) {
	   if (Context->getSourceManager().isInSystemHeader(FuncDecl->getLocation()) || FuncDecl->isImplicit()){
	       printMsg(cl,sysFuncs[i],SysFailType);
	   }
         }
       }
     }
    return true;
  }

private:
  ASTContext *Context;
};

class FindNamedCallConsumer : public clang::ASTConsumer {
public:
  explicit FindNamedCallConsumer(ASTContext *Context) : Visitor(Context) {}

  virtual void HandleTranslationUnit(clang::ASTContext &Context) {
    Visitor.TraverseDecl(Context.getTranslationUnitDecl());
  }

private:
  UsedVar Visitor;
};

class FindNamedCallAction : public clang::ASTFrontendAction {
public:
  FindNamedCallAction() {}

  virtual std::unique_ptr<clang::ASTConsumer>
  CreateASTConsumer(clang::CompilerInstance &Compiler, llvm::StringRef InFile) {

    return std::unique_ptr<clang::ASTConsumer>(
        new FindNamedCallConsumer(&Compiler.getASTContext()));
  }
};

static llvm::cl::OptionCategory MyToolCategory("my-tool options");

int main(int argc, const char **argv) {

  cl::ParseCommandLineOptions((argc-1),argv);
  
  
   //outs()<<StringAllChecks<<"\n";
   //outs()<<StrCmpCheck<<"\n";
   //outs()<<SystemAllChecks<<"\n";
  
  CommonOptionsParser OptionsParser(argc, argv, MyToolCategory);

  if(AllChecks){
    	StringAllChecks=true;
    	SystemAllChecks=true;
  }

  //outs()<<StringAllChecks<<"\n";
  //outs()<<StrCmpCheck<<"\n";
  //outs()<<SystemAllChecks<<"\n";


  ClangTool Tool(OptionsParser.getCompilations(),
                 OptionsParser.getSourcePathList());

  // run the Clang Tool, creating a new FrontendAction (explained below)
  int result = Tool.run(newFrontendActionFactory<FindNamedCallAction>().get());
  return FAIL;
}
