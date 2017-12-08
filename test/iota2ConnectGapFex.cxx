/*=========================================================================

  Program:   gapfilling
  Language:  C++

  Copyright (c) Jordi Inglada. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#include "otbWrapperApplicationRegistry.h"

int connectGapFex(int argc, char * argv[])
{
  if(argc<4)
    {
    std::cerr<<"Usage: "<<argv[0]<<" application_path infname outfname"<<std::endl;
    return EXIT_FAILURE;
    }

  std::string path = argv[1];
  std::string infname = argv[2];
  std::string outfname = argv[3];

  otb::Wrapper::ApplicationRegistry::SetApplicationPath(path);
 
  otb::Wrapper::Application::Pointer app1 = otb::Wrapper::ApplicationRegistry::CreateApplication("ImageTimeSeriesGapFilling");

  otb::Wrapper::Application::Pointer app2 = otb::Wrapper::ApplicationRegistry::CreateApplication("iota2FeatureExtraction");

  if(app1.IsNull())
    {
    std::cerr<<"Failed to create gapfilling"<<std::endl;
    return EXIT_FAILURE;
    }
  if(app2.IsNull())
    {
    std::cerr<<"Failed to create fex"<<std::endl;
    return EXIT_FAILURE;
    }

  app1->SetParameterString("in",infname);
  app1->SetParameterString("mask",infname);
  app1->SetParameterInt("comp",7);
  app1->Execute();
 
  app2->SetParameterInt("comp", 7);
  app2->SetParameterInt("red", 4);
  app2->SetParameterInt("nir", 5);
  app2->SetParameterInt("swir", 6);
  app2->SetParameterFloat("indfact", 1.0);
  app2->SetParameterString("out",outfname);

  // Connect app1 to app2
  app2->SetParameterInputImage("in",app1->GetParameterOutputImage("out"));

  app2->ExecuteAndWriteOutput();
  return EXIT_SUCCESS;
}
