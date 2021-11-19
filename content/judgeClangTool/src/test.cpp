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

using namespace clang;
using namespace clang::tooling;
using namespace llvm;

cl::opt<bool> StringAllChecks("string-all-check",cl::desc("Enables all string checks"),cl::init(false));
cl::opt<bool> StrCmpCheck("strcmp-check",cl::desc("Enables strcmp  checks"),cl::init(false));
cl::opt<bool> SystemAllChecks("sys-all-check",cl::desc("Enables all system checks"),cl::init(false));

enum FAILTYPE{
  NoFailure=0,
  StringFailType=20,
  SysFailType=30 
};

static FAILTYPE FAIL=NoFailure;

static const char *strFuncs[] = {
    "strlen", "strcat",  "strncat", "strcpy",  "strncpy", "strcmp",  "strncmp",
    "strchr", "strrchr", "strstr",  "strcspn", "strspn",  "strpbrk", "strtok"};

class UsedVar : public RecursiveASTVisitor<UsedVar> {

public:
  size_t length;
  explicit UsedVar(ASTContext *Context) : Context(Context) {
    length = sizeof(strFuncs) / sizeof(strFuncs[0]);
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
    // Only function definitions (with bodies), not declarations.
    auto FuncDecl = cl->getDirectCallee();
    if(StringAllChecks){
     for (int i = 0; i < length; i++) {
        if (FuncDecl && FuncDecl->getNameInfo().getAsString() == strFuncs[i]) {
        // if (Context->getSourceManager().isInMainFile(f->getLocation()))
        // llvm::outs() << f->getNameInfo().getAsString() << "\n";
         if (Context->getSourceManager().isInSystemHeader(FuncDecl->getLocation()))
          // llvm::outs() << FuncDecl->getNameInfo().getAsString() << "\n";
             printMsg(cl,strFuncs[i],StringFailType);
        }
      }
    }
    else if(StrCmpCheck){
      if (FuncDecl && FuncDecl->getNameInfo().getAsString() == "strcmp") {
         if (Context->getSourceManager().isInSystemHeader(FuncDecl->getLocation()))
             printMsg(cl,"strcmp",StringFailType);
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

  ClangTool Tool(OptionsParser.getCompilations(),
                 OptionsParser.getSourcePathList());

  // run the Clang Tool, creating a new FrontendAction (explained below)
  int result = Tool.run(newFrontendActionFactory<FindNamedCallAction>().get());
  return FAIL;
}
