#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/ParentMap.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Analysis/CFG.h"
#include "clang/Analysis/CFGStmtMap.h"
#include "clang/Driver/Options.h"
#include "clang/Frontend/ASTConsumers.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"

#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/FileManager.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Basic/TargetInfo.h"
#include "clang/Basic/TargetOptions.h"

#include "clang/Lex/Preprocessor.h"
#include "clang/Parse/ParseAST.h"

#include "clang/Rewrite/Frontend/Rewriters.h"
#include "llvm/Support/Host.h"
#include "llvm/Support/raw_ostream.h"

#include <bits/stdc++.h>
#include <string.h>

using namespace clang;
using namespace clang::tooling;

static const char *strFuncs[] = {
    "strlen", "strcat",  "strncat", "strcpy",  "strncpy", "strcmp",  "strncmp",
    "strchr", "strrchr", "strstr",  "strcspn", "strspn",  "strpbrk", "strtok"};

class UsedVar : public RecursiveASTVisitor<UsedVar> {

public:
  size_t length;
  explicit UsedVar(ASTContext *Context) : Context(Context) {
    length = sizeof(strFuncs) / sizeof(strFuncs[0]);
  }

  void printMsg(Stmt *qst) {

    FullSourceLoc FullLocation = Context->getFullLoc(qst->getBeginLoc());
    if (FullLocation.isValid() && !FullLocation.isInSystemHeader())
      llvm::outs() << "strcmp used at line number: "
                   << FullLocation.getSpellingLineNumber() << ":"
                   << FullLocation.getSpellingColumnNumber() << "\n";
  }

  bool VisitCallExpr(CallExpr *cl) {
    // Only function definitions (with bodies), not declarations.
    auto FuncDecl = cl->getDirectCallee();
    for (int i = 0; i < length; i++) {
      if (FuncDecl && FuncDecl->getNameInfo().getAsString() == strFuncs[i]) {
        // if (Context->getSourceManager().isInMainFile(f->getLocation()))
        // llvm::outs() << f->getNameInfo().getAsString() << "\n";
        if (Context->getSourceManager().isInSystemHeader(
                FuncDecl->getLocation()))
          // llvm::outs() << FuncDecl->getNameInfo().getAsString() << "\n";
          printMsg(cl);
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

  CommonOptionsParser OptionsParser(argc, argv, MyToolCategory);
  ClangTool Tool(OptionsParser.getCompilations(),
                 OptionsParser.getSourcePathList());

  // run the Clang Tool, creating a new FrontendAction (explained below)
  int result = Tool.run(newFrontendActionFactory<FindNamedCallAction>().get());
  return result;
}
